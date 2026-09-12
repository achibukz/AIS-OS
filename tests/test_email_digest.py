import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import email_digest as ed


def test_missing_gws_binary_exits_nonzero(monkeypatch, tmp_path, capsys):
    missing = tmp_path / "gws"
    monkeypatch.setattr(ed, "GWS_BIN", missing)
    monkeypatch.setattr("sys.argv", ["email_digest.py", "--dry-run"])

    assert ed.main() == 1
    assert str(missing) in capsys.readouterr().err


def test_no_code_path_attempts_to_read_a_token_file():
    source = (Path(__file__).resolve().parents[1] / "scripts" / "email_digest.py").read_text()
    assert "google_token" not in source
    for banned in ("google.oauth2", "googleapiclient", "google.auth"):
        assert banned not in source
    for acc in ed.ACCOUNT_CONFIGS:
        assert "tokens" not in acc
        assert "token" not in acc


def test_email_fetch_never_accesses_token_files(monkeypatch):
    opened_files = []
    real_open = Path.open

    def tracking_open(path_obj, *args, **kwargs):
        opened_files.append(str(path_obj))
        return real_open(path_obj, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)
    ed.fetch_account_emails(account_type="school", gws_profile="dlsu")
    assert not any("google_token" in f for f in opened_files)

TZ = ZoneInfo("Asia/Manila")


class TestCleanSender:
    def test_parses_display_name_with_brackets(self):
        assert ed.clean_sender("Dr. Briane Samson <briane.samson@dlsu.edu.ph>") == "Dr. Briane Samson"

    def test_parses_quoted_display_name(self):
        assert ed.clean_sender('"ING Hubs Philippines HR" <hr@ing.com>') == "ING Hubs Philippines HR"

    def test_falls_back_to_raw_when_no_bracket(self):
        assert ed.clean_sender("recruiter@tech.com") == "recruiter@tech.com"


class TestNoiseFiltering:
    def test_filters_routine_hda_am_pm(self):
        assert ed.is_noise(
            from_hdr="Help Desk Announcement <helpdesk@dlsu.edu.ph>",
            subject="[HDA for Community] 19 August 2026 | PM",
            snippet="Here are the routine announcements for the DLSU community today.",
            account_type="school",
        ) is True

    def test_keeps_hda_with_suspension(self):
        assert ed.is_noise(
            from_hdr="Help Desk Announcement <helpdesk@dlsu.edu.ph>",
            subject="[HDA for Community] Class Suspension - Manila Campus",
            snippet="Please be advised that classes are suspended due to heavy rain.",
            account_type="school",
        ) is False

    def test_keeps_hda_with_typhoon_warning(self):
        assert ed.is_noise(
            from_hdr="Help Desk Announcement <helpdesk@dlsu.edu.ph>",
            subject="[HDA for Community] Weather Advisory: Typhoon Signal No. 2",
            snippet="DLSU Manila shifting to full online classes.",
            account_type="school",
        ) is False

    def test_filters_laguna_only_notices(self):
        assert ed.is_noise(
            from_hdr="Campus Admin <admin@dlsu.edu.ph>",
            subject="Power Interruption at Laguna Campus",
            snippet="Scheduled maintenance for Laguna Campus buildings only.",
            account_type="school",
        ) is True

    def test_keeps_laguna_if_manila_included(self):
        assert ed.is_noise(
            from_hdr="Campus Admin <admin@dlsu.edu.ph>",
            subject="Intercampus Shuttle Service: Laguna and Manila Campuses",
            snippet="Updated schedule for Manila and Laguna routes.",
            account_type="school",
        ) is False

    def test_filters_linkedin_job_alerts(self):
        assert ed.is_noise(
            from_hdr="LinkedIn Job Alerts <jobalerts-noreply@linkedin.com>",
            subject="[January 2027 Start Date] Information Technology Internship at Procter & Gamble",
            snippet="30 new jobs match your preferences.",
            account_type="work",
        ) is True

    def test_filters_linkedin_connection_acceptances(self):
        assert ed.is_noise(
            from_hdr="Arvin Joseph De Leon via LinkedIn <invitations@linkedin.com>",
            subject="Arvin Joseph accepted your invitation, explore their network",
            snippet="See who else you know in common.",
            account_type="work",
        ) is True

    def test_filters_marketing_and_promotions(self):
        assert ed.is_noise(
            from_hdr="Grammarly Insights <insights@grammarly.com>",
            subject="Time to jump back in!",
            snippet="Check out your weekly writing streak.",
            account_type="school",
        ) is True

        assert ed.is_noise(
            from_hdr="Tonik Bank <promos@tonikbank.com>",
            subject="Hey luv, we're here to support every gastos!",
            snippet="Get 5% cashback on all purchases.",
            account_type="work",
        ) is True


class TestCategorization:
    def test_categorizes_prof_and_recommendation_as_priority(self):
        item = ed.categorize_email(
            from_hdr="Dr. Briane Samson <briane.samson@dlsu.edu.ph>",
            subject="Re: Recommendation Letter Request for Aki Bukuhan",
            snippet="Hi Aki, I have submitted the recommendation letter.",
            account_type="school",
        )
        assert item == "priority"

    def test_categorizes_manila_suspension_as_priority(self):
        item = ed.categorize_email(
            from_hdr="Help Desk Announcement <helpdesk@dlsu.edu.ph>",
            subject="[HDA for Community] Manila Campus Class Suspension Announcement",
            snippet="All face-to-face classes in Manila are suspended.",
            account_type="school",
        )
        assert item == "priority"

    def test_categorizes_animospace_as_academic(self):
        item = ed.categorize_email(
            from_hdr="AnimoSpace Notifications <notifications@instructure.com>",
            subject="STCLOUD: Assignment 2 Submissions Open",
            snippet="New assignment has been posted by your instructor.",
            account_type="school",
        )
        assert item == "academic"

    def test_categorizes_iteo_as_academic(self):
        item = ed.categorize_email(
            from_hdr="ITEO - Evaluation <iteo@dlsu.edu.ph>",
            subject="Online Evaluation for Term 3, AY 2025 - 2026",
            snippet="Please complete your faculty evaluation before the deadline.",
            account_type="school",
        )
        assert item == "academic"

    def test_categorizes_ing_internship_as_priority(self):
        item = ed.categorize_email(
            from_hdr="ING Hubs Philippines Talent Acquisition <talent@ing.com>",
            subject="Retail Tech Internship - Onboarding Checklist and Requirements",
            snippet="Welcome Aki! Please review and submit your pre-employment documents.",
            account_type="work",
        )
        assert item == "priority"

    def test_categorizes_vanscell_ing_email_as_priority(self):
        item = ed.categorize_email(
            from_hdr='"Nierra, Vanscell" <vanscell.nierra@ing.com>',
            subject="Internship Offer Letter Access Details",
            snippet="Please see attached instructions for your ING offer letter access.",
            account_type="work",
        )
        assert item == "priority"

    def test_github_pr_not_noise_despite_unsubscribe_footer(self):
        assert ed.is_noise(
            from_hdr="Anthony Andrei Tan <notifications@github.com>",
            subject="Re: [achibukz/opus-subagents] Add an install path for a new collaborator (PR #1)",
            snippet="@anthonyandrei requested your review on: achibukz/opus-subagents#1. — Reply to this email directly, view it on GitHub, or unsubscribe.",
            account_type="work",
        ) is False

    def test_categorizes_github_pr_review_as_priority(self):
        item = ed.categorize_email(
            from_hdr="Anthony Andrei Tan <notifications@github.com>",
            subject="Re: [achibukz/opus-subagents] Add an install path for a new collaborator (PR #1)",
            snippet="@anthonyandrei requested your review on: achibukz/opus-subagents#1.",
            account_type="work",
        )
        assert item == "priority"

    def test_categorizes_security_alerts_as_priority(self):
        item = ed.categorize_email(
            from_hdr="Tonik Bank Security <security@tonikbank.com>",
            subject="Our security update is live tomorrow, luv!",
            snippet="Important security update regarding your account authentication.",
            account_type="work",
        )
        assert item == "priority"


class TestMessageBuilder:
    def test_builds_empty_inbox_message(self):
        msg = ed.build_account_message_raw("🎓 DLSU School Email", "school", [], 5)
        assert "🍃 Inbox clear." in msg
        assert "Filtered 5 routine/promotional emails." in msg

    def test_builds_structured_school_message_with_priority_and_academics(self):
        items = [
            ed.EmailItem(
                sender="Dr. Briane Samson",
                subject="Re: Recommendation Letter Request",
                snippet="Hi Aki, I have submitted the letter for your application.",
                category="priority",
            ),
            ed.EmailItem(
                sender="ITEO - Evaluation",
                subject="Online Evaluation for Term 3",
                snippet="Please complete your student evaluation of professors.",
                category="academic",
            ),
        ]
        msg = ed.build_account_message_raw("🎓 DLSU School Email", "school", items, 3)
        assert "⚡ HIGH PRIORITY & VIP:" in msg
        assert "• Dr. Briane Samson — Re: Recommendation Letter Request" in msg
        assert "📚 COURSES & ACADEMICS:" in msg
        assert "• ITEO - Evaluation — Online Evaluation for Term 3" in msg
        assert "💡 2 items surfaced • 3 routine/promo emails filtered" in msg


class TestEmailSourceLinks:
    def test_multiple_accounts_web_link_formatting(self):
        # DLSU account
        item_dlsu = ed.EmailItem(
            sender="Dr. Briane Samson",
            subject="Recommendation Letter",
            snippet="Submitted.",
            message_id="191e4f3a",
            account_email="abram_bukuhan@dlsu.edu.ph",
        )
        assert item_dlsu.web_link == "https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/191e4f3a"
        assert ed.format_source_link(item_dlsu) == '<a href="https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/191e4f3a">[link]</a>'

        # Work account with thread_id
        item_work = ed.EmailItem(
            sender="Vanscell Nierra",
            subject="Offer Details",
            snippet="Offer attached.",
            thread_id="thread987",
            account_email="akibukzwork@gmail.com",
        )
        assert item_work.web_link == "https://mail.google.com/mail/u/akibukzwork@gmail.com/#all/thread987"
        assert ed.format_source_link(item_work) == '<a href="https://mail.google.com/mail/u/akibukzwork@gmail.com/#all/thread987">[link]</a>'

        # Personal account
        item_personal = ed.EmailItem(
            sender="Tonik Bank",
            subject="Security Alert",
            snippet="Login detected.",
            message_id="sec456",
            account_email="akibukuhan10@gmail.com",
        )
        assert item_personal.web_link == "https://mail.google.com/mail/u/akibukuhan10@gmail.com/#all/sec456"
        assert ed.format_source_link(item_personal) == '<a href="https://mail.google.com/mail/u/akibukuhan10@gmail.com/#all/sec456">[link]</a>'

    def test_absent_id_reports_missing_identity_without_guessing(self):
        item_no_id = ed.EmailItem(
            sender="Samson",
            subject="Thesis update",
            snippet="Please check draft.",
            account_email="abram_bukuhan@dlsu.edu.ph",
        )
        assert item_no_id.web_link is None
        assert ed.format_source_link(item_no_id) == "[missing ID]"

        # Verify fallback message uses [missing ID] and never guesses a search link
        msg = ed.build_account_message_raw("🎓 DLSU School Email", "school", [item_no_id], 0)
        assert "[missing ID]" in msg
        assert "mail.google.com" not in msg

    def test_model_omitted_link_is_attached_by_structured_renderer(self, monkeypatch):
        item = ed.EmailItem(
            sender="Dr. Briane Samson",
            subject="Re: Recommendation Letter Request",
            snippet="Submitted your letter.",
            category="priority",
            message_id="msg001",
            account_email="abram_bukuhan@dlsu.edu.ph",
        )
        llm_output = (
            "⚡ HIGH PRIORITY & VIP\n"
            "• Dr. Briane Samson — Re: Recommendation Letter Request\n"
            "      Dr. Samson confirmed submission of your recommendation letter."
        )
        monkeypatch.setattr(ed, "synthesize_account_emails_llm", lambda *args, **kwargs: llm_output)

        msg = ed.build_account_message("🎓 DLSU School Email", "school", [item], 0, raw_mode=False)
        assert '<a href="https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/msg001">[link]</a>' in msg
        assert "Dr. Samson confirmed submission" in msg

    def test_model_invented_link_is_replaced_by_valid_source_link(self, monkeypatch):
        item = ed.EmailItem(
            sender="Vanscell Nierra",
            subject="Offer access",
            snippet="Review document.",
            category="priority",
            message_id="valid_msg_id",
            account_email="akibukzwork@gmail.com",
        )
        llm_output_with_fake_link = (
            "⚡ HIGH PRIORITY & VIP\n"
            '• Vanscell Nierra — Offer access <a href="https://phishing.evil.com/steal">[link]</a>\n'
            "      Review onboarding offer letter."
        )
        monkeypatch.setattr(ed, "synthesize_account_emails_llm", lambda *args, **kwargs: llm_output_with_fake_link)

        msg = ed.build_account_message("💼 Work / Career Email", "work", [item], 0, raw_mode=False)
        assert "https://phishing.evil.com/steal" not in msg
        assert '<a href="https://mail.google.com/mail/u/akibukzwork@gmail.com/#all/valid_msg_id">[link]</a>' in msg

    def test_model_invented_link_with_absent_id_reports_missing_identity(self, monkeypatch):
        item = ed.EmailItem(
            sender="Vanscell Nierra",
            subject="Offer access",
            snippet="Review document.",
            category="priority",
            message_id="",
            thread_id="",
            account_email="akibukzwork@gmail.com",
        )
        llm_output_with_fake_link = (
            "⚡ HIGH PRIORITY & VIP\n"
            '• Vanscell Nierra — Offer access <a href="https://mail.google.com/mail/u/fake/#all/fake">[link]</a>\n'
            "      Review onboarding offer letter."
        )
        monkeypatch.setattr(ed, "synthesize_account_emails_llm", lambda *args, **kwargs: llm_output_with_fake_link)

        msg = ed.build_account_message("💼 Work / Career Email", "work", [item], 0, raw_mode=False)
        assert "https://mail.google.com/mail/u/fake/#all/fake" not in msg
        assert "[missing ID]" in msg

    def test_raw_fallback_retains_items_and_valid_links(self, monkeypatch):
        items = [
            ed.EmailItem(
                sender="Dr. Briane Samson",
                subject="Thesis Review",
                snippet="Review comments.",
                category="priority",
                message_id="m_thesis",
                account_email="abram_bukuhan@dlsu.edu.ph",
            ),
            ed.EmailItem(
                sender="Canvas Notifications",
                subject="CSOPESY Assignment",
                snippet="Quiz 1 posted.",
                category="academic",
                message_id="m_quiz",
                account_email="abram_bukuhan@dlsu.edu.ph",
            ),
        ]
        # Simulate LLM crash/failure returning None
        monkeypatch.setattr(ed, "synthesize_account_emails_llm", lambda *args, **kwargs: None)

        msg = ed.build_account_message("🎓 DLSU School Email", "school", items, 2, raw_mode=False)
        assert '<a href="https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/m_thesis">[link]</a>' in msg
        assert '<a href="https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/m_quiz">[link]</a>' in msg
        assert "⚡ HIGH PRIORITY & VIP:" in msg
        assert "📚 COURSES & ACADEMICS:" in msg

    def test_html_escaping_protects_against_markup_injection(self):
        item = ed.EmailItem(
            sender="Dr. Samson <samson@dlsu.edu.ph>",
            subject="Re: <THS-ST1> & Defense Plan",
            snippet="Score > 90 & remarks <approved>",
            category="priority",
            message_id="safe_id_123",
            account_email="abram_bukuhan@dlsu.edu.ph",
        )
        msg = ed.build_account_message_raw("🎓 DLSU School Email", "school", [item], 0)
        assert "&lt;THS-ST1&gt; &amp; Defense Plan" in msg
        assert "Score &gt; 90 &amp; remarks &lt;approved&gt;" in msg
        assert '<a href="https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/safe_id_123">[link]</a>' in msg
        # Ensure no unescaped brackets exist other than <a> tags
        import re
        cleaned = re.sub(r'<a href="[^"]+">\[link\]</a>', '', msg)
        assert "<" not in cleaned and ">" not in cleaned

    def test_long_split_preserves_anchors_across_chunks(self):
        items = [
            ed.EmailItem(
                sender=f"Sender {i}",
                subject=f"Subject {i} with some descriptive information",
                snippet=f"Snippet content for email number {i} with several details to increase length.",
                category="priority",
                message_id=f"msg{i:04d}",
                account_email="akibukzwork@gmail.com",
            )
            for i in range(25)
        ]
        msg = ed.build_account_message_raw("💼 Work / Career Email", "work", items, 0)
        # Split with small limit to force multiple chunks
        chunks = ed.split_digest_message(msg, limit=500)
        assert len(chunks) > 1
        assert sum(chunk.count("<a href=") for chunk in chunks) == 25
        joined_chunks = "".join(chunks)
        for i in range(25):
            assert f"msg{i:04d}" in joined_chunks
        for idx, chunk in enumerate(chunks):
            assert len(chunk) <= 500
            # Every chunk must have matched <a> and </a>
            open_count = chunk.count("<a href=")
            close_count = chunk.count("</a>")
            assert open_count == close_count, f"Chunk {idx} has mismatched anchor tags: {chunk}"

    def test_bracketed_number_in_subject_does_not_mismatch_item_index(self):
        items = [
            ed.EmailItem(
                sender="Prof A",
                subject="Syllabus and Policies",
                snippet="Check the syllabus.",
                category="academic",
                message_id="id_0",
                account_email="abram_bukuhan@dlsu.edu.ph",
            ),
            ed.EmailItem(
                sender="Canvas Notifications",
                subject="[CSOPESY] Project [1] Submission",
                snippet="Submission deadline is Friday.",
                category="academic",
                message_id="id_1",
                account_email="abram_bukuhan@dlsu.edu.ph",
            ),
        ]
        bullet = "• Canvas Notifications — [CSOPESY] Project [1] Submission"
        idx, matched = ed.match_bullet_to_item(bullet, items, set())
        assert idx == 1
        assert matched == items[1]

    def test_course_code_brackets_preserved_in_llm_digest(self, monkeypatch):
        item = ed.EmailItem(
            sender="Dr. Samson",
            subject="[CSOPESY] Midterm Exam Schedule",
            snippet="Midterm exam will be next week.",
            category="priority",
            message_id="exam123",
            account_email="abram_bukuhan@dlsu.edu.ph",
        )
        llm_output = (
            "⚡ HIGH PRIORITY & VIP\n"
            "• Dr. Samson — [CSOPESY] Midterm Exam Schedule\n"
            "      Exam scheduled next week."
        )
        monkeypatch.setattr(ed, "synthesize_account_emails_llm", lambda *args, **kwargs: llm_output)
        msg = ed.build_account_message("🎓 DLSU School Email", "school", [item], 0, raw_mode=False)
        assert "[CSOPESY] Midterm Exam Schedule" in msg
        assert '<a href="https://mail.google.com/mail/u/abram_bukuhan@dlsu.edu.ph/#all/exam123">[link]</a>' in msg

    def test_separator_lines_and_bullet_starting_with_keyword_do_not_corrupt_sections(self, monkeypatch):
        item_priority = ed.EmailItem(
            sender="Boss",
            subject="Updates & General notes on Roadmap",
            snippet="Please review roadmap updates.",
            category="priority",
            message_id="msg_priority",
            account_email="akibukzwork@gmail.com",
        )
        item_general = ed.EmailItem(
            sender="Colleague",
            subject="Lunch tomorrow",
            snippet="Are we getting lunch?",
            category="general",
            message_id="msg_general",
            account_email="akibukzwork@gmail.com",
        )
        llm_output = (
            "⚡ HIGH PRIORITY & VIP\n"
            "---\n"
            "• Boss — Updates & General notes on Roadmap\n"
            "      Review roadmap updates immediately.\n"
            "\n"
            "📬 UPDATES & GENERAL\n"
            "• Colleague — Lunch tomorrow\n"
            "      Lunch meetup inquiry."
        )
        monkeypatch.setattr(ed, "synthesize_account_emails_llm", lambda *args, **kwargs: llm_output)
        msg = ed.build_account_message("💼 Work / Career Email", "work", [item_priority, item_general], 0, raw_mode=False)
        lines = msg.splitlines()
        high_idx = next(i for i, line in enumerate(lines) if "HIGH PRIORITY" in line)
        updates_idx = next(i for i, line in enumerate(lines) if "UPDATES & GENERAL" in line)
        boss_idx = next(i for i, line in enumerate(lines) if "Boss" in line)
        colleague_idx = next(i for i, line in enumerate(lines) if "Colleague" in line)

        assert high_idx < boss_idx < updates_idx < colleague_idx

    def test_dead_profile_surfaces_warning_while_unaffected_accounts_render(self, monkeypatch):
        # dlsu profile has error, work profile has valid email
        def mock_fetch(account_type="general", gws_profile=None, account_email=None):
            if gws_profile == "dlsu":
                return [], 0, "gws dlsu error: token expired"
            if gws_profile == "work":
                item = ed.EmailItem(
                    sender="ING Hubs HR",
                    subject="Onboarding details",
                    snippet="Submit requirements.",
                    category="priority",
                    message_id="work_msg_1",
                    account_email="akibukzwork@gmail.com",
                )
                return [item], 0, None
            return [], 0, None

        monkeypatch.setattr(ed, "fetch_account_emails", mock_fetch)

        messages = []
        monkeypatch.setattr(ed, "build_account_message", lambda title, account_type, items, noise_count, raw_mode=False, error=None: (
            messages.append((title, error, items)) or f"MSG FOR {title} error={error}"
        ))
        monkeypatch.setattr("sys.argv", ["email_digest.py", "--dry-run"])
        ed.main()

        dlsu_entry = next((t, err, items) for t, err, items in messages if "DLSU" in t)
        work_entry = next((t, err, items) for t, err, items in messages if "Work" in t)

        assert dlsu_entry[1] == "gws dlsu error: token expired"
        assert len(dlsu_entry[2]) == 0

        assert work_entry[1] is None
        assert len(work_entry[2]) == 1
        assert work_entry[2][0].message_id == "work_msg_1"

    def test_no_credentials_or_private_auth_parameters_enter_links(self):
        item_inject = ed.EmailItem(
            sender="Attacker",
            subject="Hack",
            snippet="x",
            message_id="123?access_token=secret_token&bearer=xyz",
            account_email="akibukzwork@gmail.com",
        )
        assert item_inject.web_link is None
        assert ed.format_source_link(item_inject) == "[missing ID]"

        item_bad_email = ed.EmailItem(
            sender="Attacker",
            subject="Hack",
            snippet="x",
            message_id="123",
            account_email="user@gmail.com?auth=token",
        )
        assert item_bad_email.web_link is None
        assert ed.format_source_link(item_bad_email) == "[missing ID]"


class _Done:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class TestLlmChain:
    @pytest.fixture(autouse=True)
    def _llm_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(ed, "LLM_DIR", tmp_path / "llm")

    def test_falls_back_to_claude_when_agy_is_missing(self, monkeypatch, capsys):
        calls = []

        def fake_run(argv, **kwargs):
            calls.append(argv[0])
            assert kwargs["stdin"] is ed.subprocess.DEVNULL
            if argv[0] == str(ed.AGY_BIN):
                raise FileNotFoundError(2, "No such file or directory", "agy")
            return _Done(stdout="• Prof — Letter\n      Reply needed.")

        monkeypatch.setattr(ed.subprocess, "run", fake_run)

        assert ed.run_llm("p", lambda out: "•" in out) == "• Prof — Letter\n      Reply needed."
        assert calls == [str(ed.AGY_BIN), str(ed.CLAUDE_BIN)]
        err = capsys.readouterr().err
        assert "agy gemini-3.8-flash failed" in err
        assert "used claude haiku" in err

    def test_reads_codex_answer_from_its_output_file(self, monkeypatch):
        def fake_run(argv, **kwargs):
            if argv[0] == str(ed.AGY_BIN):
                return _Done(returncode=1, stderr="quota exhausted")
            if argv[0] == str(ed.CLAUDE_BIN):
                raise ed.subprocess.TimeoutExpired(argv, 60)
            Path(argv[argv.index("-o") + 1]).write_text("INBOX_CLEAR\n")
            return _Done(stdout="")

        monkeypatch.setattr(ed.subprocess, "run", fake_run)

        assert ed.run_llm("p", lambda out: out == "INBOX_CLEAR") == "INBOX_CLEAR"

    def test_chain_passes_the_pinned_models_and_efforts(self, tmp_path):
        chain = ed.llm_chain("p", tmp_path / "out.txt")
        agy, claude, codex = (argv for _, argv, _ in chain)
        assert agy[agy.index("--model") + 1] == "gemini-3.8-flash"
        assert agy[agy.index("--effort") + 1] == "medium"
        assert claude[claude.index("--model") + 1] == "claude-haiku-4-5"
        assert codex[codex.index("-m") + 1] == "gpt-5.6-luna"
        assert "model_reasoning_effort=medium" in codex

    def test_every_failure_is_logged_and_none_returned(self, monkeypatch, capsys):
        monkeypatch.setattr(ed.subprocess, "run", lambda argv, **kw: _Done(stdout="no bullets here"))

        assert ed.run_llm("p", lambda out: "•" in out) is None
        err = capsys.readouterr().err
        for label in ("agy gemini-3.8-flash", "claude haiku", "codex gpt-5.6-luna"):
            assert f"LLM {label} returned unusable output" in err
        assert "every LLM in the chain failed" in err


class TestFetchErrorHandling:
    NETWORK = (
        "gws dlsu error: error[discovery]: error sending request for url "
        "(https://www.googleapis.com/discovery/v1/apis/gmail/v1/rest): client error (Connect): "
        "tcp connect error: No route to host (os error 113)"
    )

    def test_network_error_does_not_ask_for_reauth(self):
        msg = ed.build_account_message("🎓 DLSU School Email", "school", [], 0, error=self.NETWORK)
        assert "Network unavailable" in msg
        assert "re-auth" not in msg

    def test_auth_error_keeps_the_reauth_hint(self):
        msg = ed.build_account_message(
            "🎓 DLSU School Email", "school", [], 0, error="gws dlsu error: invalid_grant: Token has been expired or revoked"
        )
        assert "run re-auth" in msg

    def test_timeout_counts_as_network(self):
        assert ed.is_network_error("gws dlsu error: Command '['gws']' timed out after 10 seconds")
        assert not ed.is_network_error(None)

    def test_main_retries_a_network_failure_once(self, monkeypatch, tmp_path, capsys):
        gws = tmp_path / "gws"
        gws.write_text("")
        monkeypatch.setattr(ed, "GWS_BIN", gws)
        monkeypatch.setattr(ed.time, "sleep", lambda s: None)
        results = iter([([], 0, self.NETWORK), ([], 2, None)])
        calls = []

        def fake_fetch(**kwargs):
            calls.append(kwargs["gws_profile"])
            return next(results)

        monkeypatch.setattr(ed, "fetch_account_emails", fake_fetch)
        monkeypatch.setattr("sys.argv", ["email_digest.py", "--dry-run", "--account", "dlsu"])

        assert ed.main() == 0
        assert calls == ["dlsu", "dlsu"]
        out = capsys.readouterr().out
        assert "Inbox clear" in out
        assert "Sync Warning" not in out


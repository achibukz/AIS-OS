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

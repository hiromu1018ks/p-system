from datetime import date, timedelta
import pytest


class TestDashboardSummary:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/dashboard/summary")
        assert resp.status_code == 401

    def test_empty_dashboard(self, auth_client):
        resp = auth_client.get("/api/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["active_permissions"] == 0
        assert data["active_leases"] == 0
        assert data["expiring_soon"] == 0
        assert data["new_this_month"] == 0
        assert data["fy_total"] == 0
        assert data["status_distribution"]["permissions"] == []
        assert data["status_distribution"]["leases"] == []
        assert data["expiry_alerts"] == []
        assert data["recent_logs"] == []

    def test_active_permission_count(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="テスト公園", property_code="P0001", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        for status in ["draft", "submitted", "under_review", "pending_approval", "approved", "issued"]:
            p = Permission(
                property_id=prop.id, applicant_name=f"申請者{status}",
                applicant_address="〇〇市1-1",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status,
            )
            db_session.add(p)
        # Terminal statuses should NOT count
        for status in ["expired", "cancelled", "rejected"]:
            p = Permission(
                property_id=prop.id, applicant_name=f"終了{status}",
                applicant_address="〇〇市1-1",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status,
            )
            db_session.add(p)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_permissions"] == 6

    def test_active_lease_count(self, auth_client, db_session):
        from models.property import Property
        from models.lease import Lease

        prop = Property(name="テスト土地", property_code="P0002", property_type="general")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        for status in ["draft", "negotiating", "pending_approval", "active"]:
            l = Lease(
                property_id=prop.id, lessee_name=f"借受人{status}",
                lessee_address="〇〇市1-1",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status, property_sub_type="land",
            )
            db_session.add(l)
        for status in ["expired", "terminated"]:
            l = Lease(
                property_id=prop.id, lessee_name=f"終了{status}",
                lessee_address="〇〇市1-1",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status=status, property_sub_type="land",
            )
            db_session.add(l)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_leases"] == 4

    def test_deleted_cases_excluded(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="削除テスト", property_code="P0010", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        # Active case
        p1 = Permission(
            property_id=prop.id, applicant_name="有効",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved",
        )
        # Deleted case (should NOT count)
        p2 = Permission(
            property_id=prop.id, applicant_name="削除済み",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved", is_deleted=True,
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_permissions"] == 1

    def test_is_latest_case_false_excluded(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="最新テスト", property_code="P0011", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        # Old renewal (is_latest_case=False)
        p1 = Permission(
            property_id=prop.id, applicant_name="旧案件",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved", is_latest_case=False,
        )
        # Latest renewal (is_latest_case=True)
        p2 = Permission(
            property_id=prop.id, applicant_name="新案件",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="draft", is_latest_case=True,
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        assert resp.json()["data"]["active_permissions"] == 1

    def test_new_this_month(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="月次テスト", property_code="P0006", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        # This month
        p1 = Permission(
            property_id=prop.id, applicant_name="今月案件",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved",
        )
        # Last month (created_at will be set by DB, so we just add another one this month)
        p2 = Permission(
            property_id=prop.id, applicant_name="今月案件2",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="draft",
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        # Both were created "now" which is this month
        assert resp.json()["data"]["new_this_month"] >= 2

    def test_fy_total(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="年度テスト", property_code="P0007", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        p = Permission(
            property_id=prop.id, applicant_name="今年度案件",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
            status="approved",
        )
        db_session.add(p)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        # Created now, which is within current FY
        assert resp.json()["data"]["fy_total"] >= 1

    def test_expiry_alerts_permissions(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="アラート公園", property_code="P0003", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        today = date.today()
        # Expiring in 5 days
        p1 = Permission(
            property_id=prop.id, applicant_name="急ぎ案件",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=5),
            status="approved",
        )
        # Expiring in 60 days (should NOT appear)
        p2 = Permission(
            property_id=prop.id, applicant_name="遠い未来",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=60),
            status="approved",
        )
        # Already expired (should NOT appear)
        p3 = Permission(
            property_id=prop.id, applicant_name="期限切れ",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today - timedelta(days=1),
            status="approved",
        )
        # Rejected case (should NOT appear)
        p4 = Permission(
            property_id=prop.id, applicant_name="差戻し案件",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=3),
            status="rejected",
        )
        db_session.add_all([p1, p2, p3, p4])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        alerts = resp.json()["data"]["expiry_alerts"]
        assert len(alerts) == 1
        assert alerts[0]["days_remaining"] == 5
        assert alerts[0]["applicant_name"] == "急ぎ案件"
        assert alerts[0]["property_name"] == "アラート公園"

    def test_expiry_alerts_leases(self, auth_client, db_session):
        from models.property import Property
        from models.lease import Lease

        prop = Property(name="アラート土地", property_code="P0008", property_type="general")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        today = date.today()
        l1 = Lease(
            property_id=prop.id, lessee_name="借受人急ぎ",
            lessee_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=10),
            status="active", property_sub_type="land",
        )
        db_session.add(l1)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        alerts = resp.json()["data"]["expiry_alerts"]
        lease_alerts = [a for a in alerts if a["case_type"] == "lease"]
        assert len(lease_alerts) == 1
        assert lease_alerts[0]["days_remaining"] == 10
        assert lease_alerts[0]["property_name"] == "アラート土地"

    def test_expiry_alerts_sorted_by_urgency(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="ソートテスト", property_code="P0009", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        today = date.today()
        p1 = Permission(
            property_id=prop.id, applicant_name="10日後",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=10),
            status="approved",
        )
        p2 = Permission(
            property_id=prop.id, applicant_name="3日後",
            applicant_address="〇〇市1-1",
            purpose="テスト", start_date=date(2026, 1, 1), end_date=today + timedelta(days=3),
            status="approved",
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        alerts = resp.json()["data"]["expiry_alerts"]
        assert alerts[0]["days_remaining"] < alerts[1]["days_remaining"]

    def test_recent_logs(self, auth_client, db_session):
        from models.audit_log import AuditLog

        log = AuditLog(
            user_id=auth_client.user.id,
            action="CREATE",
            target_table="t_permission",
            target_id=99,
        )
        db_session.add(log)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        logs = resp.json()["data"]["recent_logs"]
        assert len(logs) == 1
        assert logs[0]["action"] == "CREATE"
        assert logs[0]["user_name"] == "田中太郎"

    def test_fiscal_year_label(self, auth_client):
        resp = auth_client.get("/api/dashboard/summary")
        data = resp.json()["data"]
        today = date.today()
        fy = today.year if today.month >= 4 else today.year - 1
        assert data["fy_label"] == f"R{fy % 100}年度"

    def test_status_distribution(self, auth_client, db_session):
        from models.property import Property
        from models.permission import Permission

        prop = Property(name="分布テスト", property_code="P0005", property_type="administrative")
        db_session.add(prop)
        db_session.commit()
        db_session.refresh(prop)

        for _ in range(3):
            p = Permission(
                property_id=prop.id, applicant_name="テスト",
                applicant_address="〇〇市1-1",
                purpose="テスト", start_date=date(2026, 1, 1), end_date=date(2027, 1, 1),
                status="approved",
            )
            db_session.add(p)
        db_session.commit()

        resp = auth_client.get("/api/dashboard/summary")
        dist = resp.json()["data"]["status_distribution"]["permissions"]
        approved = [d for d in dist if d["status"] == "approved"]
        assert len(approved) == 1
        assert approved[0]["count"] == 3

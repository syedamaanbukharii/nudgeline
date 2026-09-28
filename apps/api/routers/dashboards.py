"""Dashboards API router for Role-Based Access Control (RBAC) views."""

from fastapi import APIRouter, Depends, HTTPException, Request
import logging

router = APIRouter(prefix="/v1/dashboards", tags=["dashboards"])
logger = logging.getLogger(__name__)


@router.get("/team-lead")
async def get_team_lead_dashboard(req: Request):
    """
    Returns dashboard data for a Team Lead.
    Includes information on which BD members the AI called for,
    scheduled meetings (dates, times, prospect name).
    """
    tenant_id = getattr(req.state, "tenant_id", None)
    
    # MVP Mock Data: In production, query `users` where `team_id` matches the leader's team,
    # join with `calls` and `meetings`.
    return {
        "role": "team_lead",
        "team_name": "Outbound Alpha",
        "members": [
            {
                "id": "mem-1",
                "name": "Alex Rep",
                "ai_calls_today": 45,
                "meetings_booked": 2,
                "recent_meetings": [
                    {
                        "prospect_name": "John Doe (Acme Corp)",
                        "date": "2026-09-30",
                        "time": "14:00"
                    },
                    {
                        "prospect_name": "Jane Smith (Globex)",
                        "date": "2026-10-01",
                        "time": "10:30"
                    }
                ]
            },
            {
                "id": "mem-2",
                "name": "Sam Closer",
                "ai_calls_today": 30,
                "meetings_booked": 0,
                "recent_meetings": []
            }
        ]
    }


@router.get("/manager")
async def get_manager_dashboard(req: Request):
    """
    Returns dashboard data for a Manager.
    Includes team-level performance, target completion status, 
    and highlights teams falling behind.
    """
    tenant_id = getattr(req.state, "tenant_id", None)
    
    # MVP Mock Data: In production, group `calls` and `meetings` by `team_id`.
    return {
        "role": "manager",
        "organization_name": "Global Sales",
        "teams": [
            {
                "id": "team-1",
                "name": "Outbound Alpha",
                "lead_name": "Sarah Lead",
                "target_calls": 100,
                "actual_calls": 75,
                "target_meetings": 5,
                "actual_meetings": 2,
                "target_achieved": False
            },
            {
                "id": "team-2",
                "name": "Inbound Beta",
                "lead_name": "Mike Supervisor",
                "target_calls": 50,
                "actual_calls": 55,
                "target_meetings": 3,
                "actual_meetings": 4,
                "target_achieved": True
            }
        ],
        "insights": [
            "Team 'Outbound Alpha' is currently tracking behind on their meeting targets (2/5)."
        ]
    }

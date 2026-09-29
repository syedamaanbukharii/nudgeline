"use client";

import { useState, useEffect } from "react";

export default function DashboardPage() {
  const [role, setRole] = useState<"manager" | "team_lead" | "rep">("manager");
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // In production, this would use TanStack Query to fetch from 
    // /v1/dashboards/manager or /v1/dashboards/team-lead based on authenticated user's role.
    
    if (role === "manager") {
      setData({
        organization_name: "Global Sales",
        teams: [
          {
            id: "team-1",
            name: "Outbound Alpha",
            lead_name: "Sarah Lead",
            target_calls: 100,
            actual_calls: 75,
            target_meetings: 5,
            actual_meetings: 2,
            target_achieved: false
          },
          {
            id: "team-2",
            name: "Inbound Beta",
            lead_name: "Mike Supervisor",
            target_calls: 50,
            actual_calls: 55,
            target_meetings: 3,
            actual_meetings: 4,
            target_achieved: true
          }
        ],
        insights: [
          "Team 'Outbound Alpha' missed their meeting targets (2/5).",
          "Team 'Inbound Beta' over-performed on call volume (55/50)."
        ]
      });
    } else if (role === "team_lead") {
      setData({
        team_name: "Outbound Alpha",
        members: [
          {
            id: "mem-1",
            name: "Alex Rep",
            ai_calls_today: 45,
            meetings_booked: 2,
            recent_meetings: [
              { prospect_name: "John Doe (Acme Corp)", date: "2026-09-30", time: "14:00" },
              { prospect_name: "Jane Smith (Globex)", date: "2026-10-01", time: "10:30" }
            ]
          },
          {
            id: "mem-2",
            name: "Sam Closer",
            ai_calls_today: 30,
            meetings_booked: 0,
            recent_meetings: []
          }
        ]
      });
    } else {
      setData(null); // BD Rep logic would go here
    }
  }, [role]);

  return (
    <div className="space-y-8">
      {/* Role Switcher (For demonstration purposes) */}
      <div className="flex items-center space-x-4 bg-slate-100 p-4 rounded-lg border">
        <span className="font-semibold text-sm text-slate-600">Simulate Role:</span>
        <button 
          className={`px-4 py-2 text-sm rounded-md font-medium transition-colors ${role === 'manager' ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700 border'}`}
          onClick={() => setRole('manager')}
        >
          Manager
        </button>
        <button 
          className={`px-4 py-2 text-sm rounded-md font-medium transition-colors ${role === 'team_lead' ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700 border'}`}
          onClick={() => setRole('team_lead')}
        >
          Team Lead
        </button>
      </div>

      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">
          {role === 'manager' ? 'Organization Overview' : 'Team Performance'}
        </h2>
      </div>

      {role === "manager" && data && (
        <div className="space-y-6">
          <div className="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-lg text-sm">
            <span className="font-bold">Insight: </span>
            {data.insights[0]}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {data.teams.map((team: any) => (
              <div key={team.id} className="rounded-xl border bg-white shadow-sm p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-lg">{team.name}</h3>
                    <p className="text-sm text-slate-500">Lead: {team.lead_name}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-semibold rounded-full ${team.target_achieved ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                    {team.target_achieved ? 'On Track' : 'Behind Target'}
                  </span>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">AI Calls</span>
                      <span className="font-medium">{team.actual_calls} / {team.target_calls}</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, (team.actual_calls / team.target_calls) * 100)}%` }}></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Meetings Booked</span>
                      <span className="font-medium">{team.actual_meetings} / {team.target_meetings}</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${Math.min(100, (team.actual_meetings / team.target_meetings) * 100)}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {role === "team_lead" && data && (
        <div className="space-y-6">
          <h3 className="text-xl font-semibold text-slate-800">{data.team_name} - BD Members</h3>
          <div className="grid gap-6 lg:grid-cols-2">
            {data.members.map((member: any) => (
              <div key={member.id} className="rounded-xl border bg-white shadow-sm overflow-hidden">
                <div className="p-6 border-b bg-slate-50">
                  <h4 className="font-bold text-lg">{member.name}</h4>
                  <div className="mt-2 flex items-center space-x-6 text-sm text-slate-600">
                    <div><span className="font-semibold text-slate-900">{member.ai_calls_today}</span> AI Calls</div>
                    <div><span className="font-semibold text-slate-900">{member.meetings_booked}</span> Meetings Booked</div>
                  </div>
                </div>
                
                <div className="p-6">
                  <h5 className="font-semibold text-sm mb-4 text-slate-700">Upcoming Scheduled Meetings</h5>
                  {member.recent_meetings.length === 0 ? (
                    <p className="text-sm text-slate-500 italic">No meetings booked recently.</p>
                  ) : (
                    <ul className="space-y-3">
                      {member.recent_meetings.map((meeting: any, idx: number) => (
                        <li key={idx} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50">
                          <div>
                            <p className="font-medium text-sm text-indigo-900">{meeting.prospect_name}</p>
                            <p className="text-xs text-slate-500">Call assigned to {member.name}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold text-slate-700">{meeting.date}</p>
                            <p className="text-xs text-slate-500">{meeting.time}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

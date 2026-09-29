"use client";

import { useState } from "react";
import { 
  Users, 
  BarChart3, 
  PhoneCall, 
  Settings, 
  ShieldCheck, 
  PlayCircle,
  Calendar,
  CheckCircle2,
  Clock
} from "lucide-react";

export default function DashboardPage() {
  const [role, setRole] = useState<"admin" | "manager" | "rep">("rep");
  const [activeTab, setActiveTab] = useState("dashboard");

  // Mock State for AI Caller Simulation
  const [callingLead, setCallingLead] = useState<string | null>(null);

  const handleStartAICall = (leadName: string) => {
    setCallingLead(leadName);
    setTimeout(() => {
      setCallingLead(null);
      alert(`AI Call completed with ${leadName}. Meeting booked!`);
    }, 3000);
  };

  return (
    <div className="flex h-full -m-6">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-slate-900 text-slate-300 p-4 flex flex-col min-h-[calc(100vh-3.5rem)]">
        <div className="mb-8">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Role Simulation</h2>
          <div className="flex flex-col space-y-2">
            <button onClick={() => setRole("admin")} className={`px-3 py-2 text-sm text-left rounded-md transition ${role === 'admin' ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800'}`}>👑 Admin / Owner</button>
            <button onClick={() => setRole("manager")} className={`px-3 py-2 text-sm text-left rounded-md transition ${role === 'manager' ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800'}`}>📊 Team Manager</button>
            <button onClick={() => setRole("rep")} className={`px-3 py-2 text-sm text-left rounded-md transition ${role === 'rep' ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800'}`}>📞 BD Rep (Member)</button>
          </div>
        </div>

        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Menu</h2>
        <nav className="space-y-1">
          <button onClick={() => setActiveTab("dashboard")} className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-md transition ${activeTab === 'dashboard' ? 'bg-slate-800 text-white' : 'hover:bg-slate-800'}`}>
            <BarChart3 className="w-4 h-4" /> <span>Dashboard</span>
          </button>
          
          {(role === 'rep' || role === 'manager') && (
            <button onClick={() => setActiveTab("dialer")} className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-md transition ${activeTab === 'dialer' ? 'bg-slate-800 text-white' : 'hover:bg-slate-800'}`}>
              <PhoneCall className="w-4 h-4" /> <span>My Leads & Dialer</span>
            </button>
          )}

          {(role === 'manager' || role === 'admin') && (
            <button onClick={() => setActiveTab("campaigns")} className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-md transition ${activeTab === 'campaigns' ? 'bg-slate-800 text-white' : 'hover:bg-slate-800'}`}>
              <Users className="w-4 h-4" /> <span>Team Campaigns</span>
            </button>
          )}

          {role === 'admin' && (
            <>
              <button onClick={() => setActiveTab("compliance")} className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-md transition ${activeTab === 'compliance' ? 'bg-slate-800 text-white' : 'hover:bg-slate-800'}`}>
                <ShieldCheck className="w-4 h-4" /> <span>Compliance Center</span>
              </button>
              <button onClick={() => setActiveTab("settings")} className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-md transition ${activeTab === 'settings' ? 'bg-slate-800 text-white' : 'hover:bg-slate-800'}`}>
                <Settings className="w-4 h-4" /> <span>Integrations</span>
              </button>
            </>
          )}
        </nav>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-8 bg-slate-50 overflow-y-auto">
        
        {/* --- REP (MEMBER) DIALER VIEW --- */}
        {role === "rep" && activeTab === "dialer" && (
          <div className="space-y-6 max-w-5xl">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">My Leads & AI Dialer</h2>
              <p className="text-slate-500">Dispatch your AI voice agent to cold call your prospects.</p>
            </div>

            <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 border-b text-slate-600 font-semibold">
                  <tr>
                    <th className="px-6 py-4">Prospect</th>
                    <th className="px-6 py-4">Company</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {[
                    { id: 1, name: "Alice Johnson", company: "TechCorp Inc.", status: "New Lead" },
                    { id: 2, name: "Bob Smith", company: "Global Logistics", status: "Callback Requested" },
                    { id: 3, name: "Charlie Davis", company: "FinServe LLC", status: "New Lead" },
                  ].map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 font-medium text-slate-900">{lead.name}</td>
                      <td className="px-6 py-4 text-slate-600">{lead.company}</td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                          {lead.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => handleStartAICall(lead.name)}
                          disabled={callingLead === lead.name}
                          className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-sm
                            ${callingLead === lead.name 
                              ? 'bg-amber-100 text-amber-700 cursor-not-allowed' 
                              : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
                        >
                          {callingLead === lead.name ? (
                            <><Clock className="w-4 h-4 animate-spin" /> <span>AI is Calling...</span></>
                          ) : (
                            <><PlayCircle className="w-4 h-4" /> <span>Dispatch AI Call</span></>
                          )}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* --- REP (MEMBER) DASHBOARD VIEW --- */}
        {role === "rep" && activeTab === "dashboard" && (
          <div className="space-y-6 max-w-5xl">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">My Performance</h2>
              <p className="text-slate-500">Track your AI's outbound success today.</p>
            </div>
            
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">AI Calls Dispatched</p>
                <p className="text-3xl font-bold mt-2">42</p>
              </div>
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Meetings Booked</p>
                <p className="text-3xl font-bold mt-2 text-emerald-600">3</p>
              </div>
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Connect Rate</p>
                <p className="text-3xl font-bold mt-2">14%</p>
              </div>
            </div>

            <h3 className="text-lg font-bold text-slate-900 mt-8 mb-4">Upcoming Meetings (Booked by AI)</h3>
            <div className="bg-white p-6 rounded-xl border shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b pb-4">
                <div className="flex items-center space-x-4">
                  <div className="bg-indigo-100 p-3 rounded-lg text-indigo-600"><Calendar className="w-6 h-6" /></div>
                  <div>
                    <p className="font-bold text-slate-900">Demo with Alice Johnson</p>
                    <p className="text-sm text-slate-500">TechCorp Inc.</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-slate-900">Today, 2:00 PM</p>
                  <p className="text-sm text-emerald-600 font-medium">Synced to Google Calendar</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- MANAGER DASHBOARD VIEW --- */}
        {role === "manager" && activeTab === "dashboard" && (
          <div className="space-y-6 max-w-5xl">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Team Manager Dashboard</h2>
              <p className="text-slate-500">Monitor your BD Reps and active AI campaigns.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="rounded-xl border bg-white shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-4">Team: Outbound Alpha</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Total AI Calls (Today)</span>
                      <span className="font-medium">150 / 200 Target</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-indigo-500 h-2 rounded-full w-[75%]"></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Meetings Booked</span>
                      <span className="font-medium">8 / 10 Target</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full w-[80%]"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- ADMIN DASHBOARD VIEW --- */}
        {role === "admin" && activeTab === "dashboard" && (
          <div className="space-y-6 max-w-5xl">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Admin & Platform Overview</h2>
              <p className="text-slate-500">Global billing, compliance, and organization stats.</p>
            </div>

            <div className="grid grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Total Telecom Spend</p>
                <p className="text-2xl font-bold mt-2">$342.50</p>
              </div>
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">Active Reps</p>
                <p className="text-2xl font-bold mt-2">12</p>
              </div>
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">DNC Blocks</p>
                <p className="text-2xl font-bold mt-2 text-rose-600">43</p>
              </div>
              <div className="bg-white p-6 rounded-xl border shadow-sm">
                <p className="text-sm font-semibold text-slate-500">System Health</p>
                <p className="text-lg font-bold mt-2 text-emerald-600 flex items-center"><CheckCircle2 className="w-5 h-5 mr-1"/> All Systems Go</p>
              </div>
            </div>
          </div>
        )}

        {/* Fallback for empty tabs */}
        {(activeTab === "settings" || activeTab === "compliance" || activeTab === "campaigns") && (
          <div className="flex items-center justify-center h-64 border-2 border-dashed border-slate-200 rounded-xl">
            <div className="text-center">
              <h3 className="text-lg font-medium text-slate-900">Module under construction</h3>
              <p className="text-slate-500 mt-1">This specific view is coming in a future update.</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

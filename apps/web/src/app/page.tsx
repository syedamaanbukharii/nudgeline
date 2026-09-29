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
  Clock,
  Bell,
  PhoneForwarded,
  Bot,
  UserCircle,
  LogOut,
  Activity,
  Phone,
  X,
  Briefcase,
  StickyNote
} from "lucide-react";

type Lead = { id: number; name: string; company: string; status: string; history: string[] };
type Callback = { id: number; prospect: string; date: string; time: string; reason: string };
type Meeting = { id: number; prospect: string; company: string; role: string; phone: string; date: string; time: string; summary: string };

export default function DashboardPage() {
  const [role, setRole] = useState<"admin" | "manager" | "rep">("rep");
  const [activeTab, setActiveTab] = useState("dialer");

  // Mock State for AI Caller Simulation
  const [callingLead, setCallingLead] = useState<number | null>(null);
  const [customNumber, setCustomNumber] = useState("");
  
  const [leads, setLeads] = useState<Lead[]>([
    { id: 1, name: "Alice Johnson", company: "TechCorp Inc.", status: "New Lead", history: [] },
    { id: 2, name: "Bob Smith", company: "Global Logistics", status: "New Lead", history: [] },
    { id: 3, name: "Charlie Davis", company: "FinServe LLC", status: "New Lead", history: [] },
  ]);

  const [callbacks, setCallbacks] = useState<Callback[]>([
    { id: 101, prospect: "Sarah Jenkins", date: "Today", time: "3:30 PM", reason: "Prospect was boarding a flight." }
  ]);

  const [meetings, setMeetings] = useState<Meeting[]>([
    { id: 201, prospect: "John Doe", company: "Acme Corp", role: "VP of Sales", phone: "+1 (555) 019-2834", date: "Tomorrow", time: "10:00 AM", summary: "John is highly interested in the Q3 product roadmap. AI qualified him for enterprise tier." }
  ]);
  
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);

  // Derived User Identity
  const getUserProfile = () => {
    switch(role) {
      case "admin": return { name: "System Admin", email: "admin@nudgeline.com", title: "Platform Owner" };
      case "manager": return { name: "Sarah Manager", email: "sarah@nudgeline.com", title: "Outbound Alpha Lead" };
      case "rep": return { name: "Alex Rep", email: "alex@nudgeline.com", title: "BD Associate" };
    }
  };
  const user = getUserProfile();

  // Production-grade Toast Notification State
  const [toast, setToast] = useState<{ title: string; message: string; type: "success" | "info" } | null>(null);
  
  // Real-time Live Call Tracking State
  const [activeCall, setActiveCall] = useState<{ name: string; phase: string; description: string; isSpeaking: boolean } | null>(null);

  const showToast = (title: string, message: string, type: "success" | "info" = "info") => {
    setToast({ title, message, type });
    setTimeout(() => setToast(null), 6000); // auto-hide after 6s
  };

  const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

  const handleCustomCall = async () => {
    if (!customNumber) return;
    setActiveCall({ name: customNumber, phase: "Dialing...", description: "Connecting to Twilio SIP trunk", isSpeaking: false });
    await sleep(2000);
    setActiveCall({ name: customNumber, phase: "Ringing", description: "Waiting for network routing...", isSpeaking: false });
    await sleep(3000);
    setActiveCall({ name: customNumber, phase: "Failed", description: "Backend Python Voice Worker not connected yet.", isSpeaking: false });
    await sleep(2000);
    setActiveCall(null);
    showToast("Call Failed", "Cannot ring real phones until the backend LiveKit Python worker is deployed with Twilio credentials.", "info");
  };

  const handleStartAICall = async (lead: Lead) => {
    setCallingLead(lead.id);
    
    // 1. SIP Dialing Phase
    setActiveCall({ name: lead.name, phase: "Dialing...", description: "Connecting to Twilio SIP trunk", isSpeaking: false });
    await sleep(1500);
    
    // 2. Ringing Phase
    setActiveCall({ name: lead.name, phase: "Ringing", description: "Waiting for prospect to answer...", isSpeaking: false });
    await sleep(2000);
    
    if (lead.id === 1) { 
      setActiveCall({ name: lead.name, phase: "Connected", description: "AI Agent is speaking...", isSpeaking: true });
      await sleep(2000);
      setActiveCall({ name: lead.name, phase: "Connected", description: `${lead.name} is answering...`, isSpeaking: false });
      await sleep(2000);
      setActiveCall({ name: lead.name, phase: "Post-Call Processing", description: "LangGraph extracting calendar intent...", isSpeaking: false });
      await sleep(1500);
      
      showToast("Call Completed: Demo Booked!", `AI Agent successfully qualified ${lead.name} and synced the meeting to your calendar.`, "success");
      setMeetings(prev => [...prev, { id: Date.now(), prospect: lead.name, company: lead.company, role: "Director", phone: "+1 (555) 999-0000", date: "Friday", time: "11:00 AM", summary: "Alice confirmed she is looking for a new platform. Budget approved." }]);
      setLeads(prev => prev.map(l => l.id === lead.id ? { ...l, status: "Meeting Booked" } : l));
      
    } else if (lead.id === 2) {
      setActiveCall({ name: lead.name, phase: "Connected", description: "AI Agent is speaking...", isSpeaking: true });
      await sleep(1500);
      setActiveCall({ name: lead.name, phase: "Connected", description: `${lead.name} is speaking (driving)...`, isSpeaking: false });
      await sleep(2000);
      setActiveCall({ name: lead.name, phase: "Post-Call Processing", description: "LangGraph identifying callback intent...", isSpeaking: false });
      await sleep(1500);

      showToast("Call Completed: Callback Scheduled", `Transcript intent extracted via LangGraph: Prospect is driving. Callback scheduled for tomorrow morning.`, "info");
      setCallbacks(prev => [...prev, { id: Date.now(), prospect: lead.name, date: "Tomorrow", time: "9:00 AM", reason: "Prospect was driving, requested callback." }]);
      setLeads(prev => prev.map(l => l.id === lead.id ? { ...l, status: "Callback Scheduled" } : l));
      
    } else { 
      setActiveCall({ name: lead.name, phase: "Voicemail", description: "Leaving AI-generated voicemail...", isSpeaking: true });
      await sleep(3000);
      
      showToast("Call Completed: Voicemail", `AI Agent left a tailored voicemail for ${lead.name}.`, "info");
      setLeads(prev => prev.map(l => l.id === lead.id ? { ...l, status: "Left Voicemail" } : l));
    }

    setActiveCall(null);
    setCallingLead(null);
  };

  const handleManualCall = (prospect: string) => {
    showToast("Manual Dialer Initiated", `Starting SIP WebRTC connection to call ${prospect}...`, "info");
  };

  return (
    <div className="flex h-full -m-6">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-slate-900 text-slate-300 p-4 flex flex-col min-h-[calc(100vh-3.5rem)] justify-between">
        
        {/* Top Menu Section */}
        <div>
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

        {/* Bottom User Profile Section */}
        <div className="pt-4 border-t border-slate-800">
          <div className="flex items-center space-x-3 px-2">
            <div className="bg-indigo-600 p-2 rounded-full text-white">
              <UserCircle className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user.name}</p>
              <p className="text-xs text-slate-400 truncate">{user.email}</p>
            </div>
            <button className="text-slate-400 hover:text-white transition">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-8 bg-slate-50 overflow-y-auto">
        
        {/* --- REP (MEMBER) DIALER & LEADS VIEW --- */}
        {role === "rep" && activeTab === "dialer" && (
          <div className="space-y-8 max-w-6xl">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">My Leads & AI Dialer</h2>
              <p className="text-slate-500">Dispatch your AI voice agent. Outcomes (like callbacks or booked meetings) are automatically logged below.</p>
            </div>

            {/* AI Callbacks Section */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-amber-900 flex items-center mb-4">
                <Bell className="w-5 h-5 mr-2" /> Action Required: AI Scheduled Reminders & Callbacks
              </h3>
              {callbacks.length === 0 ? (
                <p className="text-sm text-amber-700 italic">No pending callbacks scheduled by AI.</p>
              ) : (
                <div className="space-y-3">
                  {callbacks.map(cb => (
                    <div key={cb.id} className="flex items-center justify-between bg-white border border-amber-100 p-4 rounded-lg shadow-sm">
                      <div className="flex items-start space-x-4">
                        <div className="bg-amber-100 p-2 rounded-full text-amber-600 mt-1"><PhoneForwarded className="w-4 h-4" /></div>
                        <div>
                          <p className="font-bold text-slate-900">Call {cb.prospect} Back</p>
                          <p className="text-sm text-slate-600 mt-1"><strong>AI Note:</strong> {cb.reason}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-amber-700">{cb.date}</p>
                        <p className="text-sm text-amber-600">{cb.time}</p>
                        <button 
                          onClick={() => handleManualCall(cb.prospect)}
                          className="mt-2 text-xs bg-amber-600 hover:bg-amber-700 text-white px-3 py-1.5 flex items-center space-x-1 rounded transition ml-auto"
                        >
                          <Phone className="w-3 h-3" /> <span>Manual Call Now</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Custom Phone Dialer */}
            <div className="bg-white rounded-xl border shadow-sm p-4 flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-800">Test Custom Number</h3>
                <p className="text-xs text-slate-500">Enter your phone number to test the real-time AI dialer routing.</p>
              </div>
              <div className="flex space-x-2">
                <input 
                  type="text" 
                  placeholder="+1 (555) 000-0000" 
                  value={customNumber}
                  onChange={(e) => setCustomNumber(e.target.value)}
                  className="border border-slate-200 rounded-lg px-3 py-2 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button 
                  onClick={handleCustomCall}
                  disabled={!customNumber}
                  className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50"
                >
                  Dial Now
                </button>
              </div>
            </div>

            {/* Leads Table */}
            <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
              <div className="p-4 border-b bg-slate-50 flex justify-between items-center">
                <h3 className="font-semibold text-slate-800">Fresh Leads Pool</h3>
              </div>
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 border-b text-slate-600 font-semibold">
                  <tr>
                    <th className="px-6 py-4">Prospect</th>
                    <th className="px-6 py-4">Company</th>
                    <th className="px-6 py-4">Last AI Status</th>
                    <th className="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {leads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 font-medium text-slate-900">{lead.name}</td>
                      <td className="px-6 py-4 text-slate-600">{lead.company}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium 
                          ${lead.status === 'New Lead' ? 'bg-blue-50 text-blue-700' : 
                            lead.status === 'Callback Scheduled' ? 'bg-amber-50 text-amber-700' :
                            lead.status === 'Meeting Booked' ? 'bg-emerald-50 text-emerald-700' :
                            'bg-slate-100 text-slate-700'}`}>
                          {lead.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => handleStartAICall(lead)}
                          disabled={callingLead === lead.id}
                          className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-sm
                            ${callingLead === lead.id 
                              ? 'bg-amber-100 text-amber-700 cursor-not-allowed' 
                              : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
                        >
                          {callingLead === lead.id ? (
                            <><Bot className="w-4 h-4 animate-bounce" /> <span>AI is on the phone...</span></>
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
            
            {/* AI Booked Meetings */}
            <div className="bg-white rounded-xl border shadow-sm p-6 mt-8">
              <h3 className="text-lg font-bold text-slate-900 mb-4 flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-indigo-600" /> Upcoming Meetings (Booked by AI)
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {meetings.map(m => (
                  <button 
                    key={m.id} 
                    onClick={() => setSelectedMeeting(m)}
                    className="border border-slate-100 bg-slate-50 hover:bg-slate-100 hover:border-slate-300 transition p-4 rounded-lg flex justify-between items-center text-left"
                  >
                    <div>
                      <p className="font-bold text-slate-900">{m.prospect}</p>
                      <p className="text-xs font-medium text-emerald-600 mt-1 flex items-center"><CheckCircle2 className="w-3 h-3 mr-1" /> Synced to Google Calendar</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-indigo-900">{m.date}</p>
                      <p className="text-sm text-slate-500">{m.time}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* --- REP DASHBOARD --- */}
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
          </div>
        )}

        {/* --- MANAGER DASHBOARD VIEW --- */}
        {role === "manager" && activeTab === "dashboard" && (
          <div className="space-y-6 max-w-5xl">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">Team Manager Dashboard</h2>
              <p className="text-slate-500">Monitor your BD Reps and active AI campaigns.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 mb-8">
              <div className="rounded-xl border bg-white shadow-sm p-6">
                <h3 className="font-semibold text-lg mb-4">Team: Outbound Alpha</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Total AI Calls (Today)</span>
                      <span className="font-medium">150 / 200 Target</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Meetings Booked</span>
                      <span className="font-medium">8 / 10 Target</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '80%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Team Members List */}
            <h3 className="text-xl font-bold text-slate-900 mb-4">Team Members</h3>
            <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 border-b text-slate-600 font-semibold">
                  <tr>
                    <th className="px-6 py-4">Rep Name</th>
                    <th className="px-6 py-4">AI Calls Dispatched</th>
                    <th className="px-6 py-4">Meetings Booked</th>
                    <th className="px-6 py-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  <tr className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium">Alex Rep</td>
                    <td className="px-6 py-4 text-slate-600">42</td>
                    <td className="px-6 py-4 text-slate-600">3</td>
                    <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full text-xs font-medium">On Target</span></td>
                  </tr>
                  <tr className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium">Sam Closer</td>
                    <td className="px-6 py-4 text-slate-600">108</td>
                    <td className="px-6 py-4 text-slate-600">5</td>
                    <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full text-xs font-medium">On Target</span></td>
                  </tr>
                </tbody>
              </table>
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

            <div className="grid grid-cols-4 gap-6 mb-8">
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

            <h3 className="text-xl font-bold text-slate-900 mb-4">Active System Integrations</h3>
            <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
              <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 border-b text-slate-600 font-semibold">
                  <tr>
                    <th className="px-6 py-4">Service</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Last Sync</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  <tr className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium flex items-center space-x-2"><Activity className="w-4 h-4 text-indigo-500" /> <span>LiveKit WebRTC</span></td>
                    <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full text-xs font-medium">Connected</span></td>
                    <td className="px-6 py-4 text-right text-slate-500">Just now</td>
                  </tr>
                  <tr className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium flex items-center space-x-2"><Bot className="w-4 h-4 text-slate-500" /> <span>Google Gemini / OpenAI</span></td>
                    <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full text-xs font-medium">Connected</span></td>
                    <td className="px-6 py-4 text-right text-slate-500">2 mins ago</td>
                  </tr>
                  <tr className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium flex items-center space-x-2"><Phone className="w-4 h-4 text-slate-500" /> <span>SIP Trunk (Twilio)</span></td>
                    <td className="px-6 py-4"><span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full text-xs font-medium">Connected</span></td>
                    <td className="px-6 py-4 text-right text-slate-500">1 hr ago</td>
                  </tr>
                </tbody>
              </table>
            </div>

          </div>
        )}

        {/* Fallback for empty/unimplemented tabs */}
        {(activeTab === "settings" || activeTab === "compliance" || activeTab === "campaigns") && (
          <div className="flex items-center justify-center h-64 border-2 border-dashed border-slate-200 rounded-xl mt-6">
            <div className="text-center">
              <h3 className="text-lg font-medium text-slate-900">Module under construction</h3>
              <p className="text-slate-500 mt-1">This specific view ({activeTab}) is coming in a future update.</p>
            </div>
          </div>
        )}

      </div>

      {/* Prospect Details Modal (Clickable Calendar) */}
      {selectedMeeting && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] flex items-center justify-center animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl w-[500px] border border-slate-200 overflow-hidden relative">
             <button onClick={() => setSelectedMeeting(null)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
             </button>
             <div className="bg-indigo-50 border-b border-indigo-100 p-6">
                <h3 className="font-bold text-2xl text-slate-900">{selectedMeeting.prospect}</h3>
                <p className="text-indigo-600 font-medium flex items-center mt-1"><Briefcase className="w-4 h-4 mr-1" /> {selectedMeeting.role} at {selectedMeeting.company}</p>
             </div>
             <div className="p-6 space-y-6">
                <div className="flex items-center space-x-4 bg-emerald-50 text-emerald-800 p-4 rounded-xl border border-emerald-100">
                  <Calendar className="w-8 h-8 text-emerald-600" />
                  <div>
                    <p className="font-bold text-sm uppercase tracking-wide text-emerald-700">Google Calendar Event Setup</p>
                    <p className="text-sm font-medium">{selectedMeeting.date} @ {selectedMeeting.time}</p>
                  </div>
                </div>
                <div>
                   <h4 className="font-semibold text-slate-900 flex items-center text-sm mb-2"><Phone className="w-4 h-4 mr-2" /> Contact Info</h4>
                   <p className="text-slate-600 text-sm font-medium bg-slate-50 border p-3 rounded-lg">{selectedMeeting.phone}</p>
                </div>
                <div>
                   <h4 className="font-semibold text-slate-900 flex items-center text-sm mb-2"><StickyNote className="w-4 h-4 mr-2" /> AI Assistant Notes & Summary</h4>
                   <p className="text-slate-600 text-sm italic bg-slate-50 border p-4 rounded-lg leading-relaxed">"{selectedMeeting.summary}"</p>
                </div>
             </div>
          </div>
        </div>
      )}

      {/* Live AI Call Tracker Modal */}
      {activeCall && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] flex items-center justify-center animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl shadow-2xl p-8 w-[400px] border border-slate-200">
             <h3 className="font-bold text-lg mb-6 text-center text-slate-900">Live AI Call Monitor</h3>
             <div className="flex flex-col items-center space-y-6">
                <div className="relative">
                  <div className={`w-20 h-20 rounded-full flex items-center justify-center ${activeCall.isSpeaking ? 'bg-indigo-100 text-indigo-600 animate-pulse' : 'bg-slate-100 text-slate-400'}`}>
                    <Activity className="w-10 h-10" />
                  </div>
                </div>
                <div className="text-center">
                  <p className="font-bold text-xl text-slate-900 mb-2">{activeCall.name}</p>
                  <p className="text-indigo-600 font-semibold text-sm uppercase tracking-wide">{activeCall.phase}</p>
                  <p className="text-slate-500 text-sm mt-1">{activeCall.description}</p>
                </div>
             </div>
          </div>
        </div>
      )}

      {/* Production Toast Notifications */}
      {toast && (
        <div className="fixed top-6 right-6 z-[110] max-w-sm w-full bg-white border border-slate-200 shadow-2xl rounded-xl p-4 flex items-start space-x-3 animate-in slide-in-from-top-5 fade-in duration-300">
          {toast.type === "success" ? (
            <div className="bg-emerald-100 text-emerald-600 p-2 rounded-full flex-shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="bg-indigo-100 text-indigo-600 p-2 rounded-full flex-shrink-0">
              <Bell className="w-5 h-5" />
            </div>
          )}
          <div>
            <h4 className="font-bold text-slate-900 text-sm">{toast.title}</h4>
            <p className="text-sm text-slate-600 mt-1">{toast.message}</p>
          </div>
        </div>
      )}

      {/* Developer Tool: Role Switcher (Floating) */}
      <div className="fixed bottom-4 right-4 bg-white p-3 rounded-xl shadow-2xl border border-slate-200 flex items-center space-x-3 z-50">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Dev Tool: Switch Role</span>
        <div className="flex space-x-1 bg-slate-100 p-1 rounded-lg">
          <button onClick={() => { setRole("admin"); setActiveTab("dashboard"); }} className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${role === 'admin' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-600 hover:bg-slate-200'}`}>Admin</button>
          <button onClick={() => { setRole("manager"); setActiveTab("dashboard"); }} className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${role === 'manager' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-600 hover:bg-slate-200'}`}>Manager</button>
          <button onClick={() => { setRole("rep"); setActiveTab("dialer"); }} className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${role === 'rep' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-600 hover:bg-slate-200'}`}>BD Rep</button>
        </div>
      </div>
    </div>
  );
}

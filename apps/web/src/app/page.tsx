export default function Home() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Mock Stat Cards */}
        <div className="rounded-xl border bg-white text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Total Calls (Today)</h3>
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">142</div>
            <p className="text-xs text-muted-foreground">+20% from yesterday</p>
          </div>
        </div>
        
        <div className="rounded-xl border bg-white text-card-foreground shadow">
          <div className="p-6 flex flex-row items-center justify-between space-y-0 pb-2">
            <h3 className="tracking-tight text-sm font-medium">Meetings Booked</h3>
          </div>
          <div className="p-6 pt-0">
            <div className="text-2xl font-bold">12</div>
          </div>
        </div>
      </div>
    </div>
  );
}

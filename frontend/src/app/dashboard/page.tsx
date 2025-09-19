export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Recent Sessions</h2>
          <p className="text-gray-600">View and manage your recent IMU analysis sessions.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">System Status</h2>
          <p className="text-gray-600">Monitor the status of your IMU processing pipeline.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Quick Actions</h2>
          <p className="text-gray-600">Start a new analysis or access frequently used tools.</p>
        </div>
      </div>
    </div>
  );
} 
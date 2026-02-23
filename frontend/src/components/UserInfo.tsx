import { User, Shield, LogOut } from 'lucide-react';
import { useAuth, PERMISSIONS } from '../contexts/AuthContext';

export default function UserInfo() {
  const { user, logout, hasPermission } = useAuth();

  if (!user) return null;

  const getRoleInfo = (role: string) => {
    switch (role) {
      case 'admin':
        return {
          label: 'Administrator',
          color: 'bg-red-100 text-red-700 border-red-200',
          icon: Shield,
          description: 'Full system access'
        };
      case 'user':
        return {
          label: 'User',
          color: 'bg-blue-100 text-blue-700 border-blue-200',
          icon: User,
          description: 'Text processing access'
        };
      default:
        return {
          label: 'Unknown',
          color: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: User,
          description: 'Limited access'
        };
    }
  };

  const roleInfo = getRoleInfo(user.role);
  const RoleIcon = roleInfo.icon;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">User Information</h3>
      
      {/* User Details */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${roleInfo.color}`}>
            <RoleIcon className="w-5 h-5" />
          </div>
          <div>
            <p className="font-medium">{user.name}</p>
            <p className="text-sm text-gray-600">@{user.username}</p>
          </div>
        </div>
        
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${roleInfo.color}`}>
          <span className="text-xs font-medium">{roleInfo.label}</span>
        </div>
        
        <p className="text-sm text-gray-600">{roleInfo.description}</p>
      </div>

      {/* Permissions */}
      <div className="mt-6">
        <h4 className="text-sm font-medium mb-3">Your Permissions:</h4>
        <div className="space-y-2">
          {hasPermission(PERMISSIONS.PROCESS_TEXT) && (
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Process Text</span>
            </div>
          )}
          {hasPermission(PERMISSIONS.PROCESS_HTML) && (
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Process HTML</span>
            </div>
          )}
          {hasPermission(PERMISSIONS.VIEW_HISTORY) && (
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>View History</span>
            </div>
          )}
          {hasPermission(PERMISSIONS.VIEW_STATISTICS) && (
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>View Statistics</span>
            </div>
          )}
          {hasPermission(PERMISSIONS.ACCESS_SETTINGS) && (
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Access Settings</span>
            </div>
          )}
          {hasPermission(PERMISSIONS.MANAGE_USERS) && (
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Manage Users</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
import { useState } from "react";
import { X, Mail, UserPlus, Check, Crown, Shield, Eye } from "lucide-react";

interface AddPeopleModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  sessionTitle: string;
}

type UserRole = "owner" | "editor" | "viewer";

interface SharedUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
}

// Mock shared users (future: fetch from API)
const MOCK_SHARED_USERS: SharedUser[] = [
  {
    id: "1",
    email: "john.doe@company.com",
    name: "John Doe",
    role: "editor",
  },
  {
    id: "2",
    email: "jane.smith@company.com",
    name: "Jane Smith",
    role: "viewer",
  },
];

export default function AddPeopleModal({
  isOpen,
  onClose,
  sessionId,
  sessionTitle,
}: AddPeopleModalProps) {
  const [email, setEmail] = useState("");
  const [selectedRole, setSelectedRole] = useState<UserRole>("viewer");
  const [sharedUsers, setSharedUsers] = useState<SharedUser[]>(MOCK_SHARED_USERS);
  const [inviteSent, setInviteSent] = useState(false);

  // Suppress unused variable warning - sessionId will be used with backend
  void sessionId;

  const handleInvite = () => {
    if (!email.trim()) return;

    // Future: API call to send invitation
    console.log("Inviting:", { email, role: selectedRole, sessionId });
    
    setInviteSent(true);
    setTimeout(() => {
      setInviteSent(false);
      setEmail("");
    }, 2000);
  };

  const handleRoleChange = (userId: string, newRole: UserRole) => {
    // Future: API call to update user role
    setSharedUsers((prev) =>
      prev.map((user) =>
        user.id === userId ? { ...user, role: newRole } : user
      )
    );
  };

  const handleRemoveUser = (userId: string) => {
    // Future: API call to remove user
    setSharedUsers((prev) => prev.filter((user) => user.id !== userId));
  };

  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case "owner":
        return <Crown className="w-4 h-4 text-amber-600" />;
      case "editor":
        return <Shield className="w-4 h-4 text-blue-600" />;
      case "viewer":
        return <Eye className="w-4 h-4 text-gray-600" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Share with people
            </h2>
            <p className="text-sm text-gray-500 mt-1 truncate max-w-md">
              {sessionTitle}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Body - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Invite Section */}
          <div>
            <label className="text-sm font-semibold text-gray-700 mb-3 block">
              Invite people
            </label>
            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="email"
                    placeholder="Enter email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    onKeyDown={(e) => e.key === "Enter" && handleInvite()}
                  />
                </div>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value as UserRole)}
                  className="px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  <option value="viewer">Can view</option>
                  <option value="editor">Can edit</option>
                </select>
              </div>

              <button
                onClick={handleInvite}
                disabled={!email.trim() || inviteSent}
                className={`w-full py-3 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${
                  inviteSent
                    ? "bg-green-50 text-green-600 border border-green-200"
                    : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                }`}
              >
                {inviteSent ? (
                  <>
                    <Check className="w-4 h-4" />
                    Invitation Sent
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    Send Invitation
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Shared With Section */}
          <div>
            <label className="text-sm font-semibold text-gray-700 mb-3 block">
              People with access
            </label>
            <div className="space-y-2">
              {sharedUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                >
                  {/* Avatar */}
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">
                      {user.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")
                        .toUpperCase()}
                    </span>
                  </div>

                  {/* User Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user.name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                  </div>

                  {/* Role Selector */}
                  {user.role === "owner" ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 rounded-lg">
                      {getRoleIcon(user.role)}
                      <span className="text-sm font-medium text-amber-900">
                        Owner
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <select
                        value={user.role}
                        onChange={(e) =>
                          handleRoleChange(user.id, e.target.value as UserRole)
                        }
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="editor">Can edit</option>
                        <option value="viewer">Can view</option>
                      </select>
                      <button
                        onClick={() => handleRemoveUser(user.id)}
                        className="p-1.5 rounded-lg hover:bg-red-50 transition-colors"
                        title="Remove access"
                      >
                        <X className="w-4 h-4 text-red-600" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Permission Descriptions */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
            <p className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Permission Levels
            </p>
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <Crown className="w-4 h-4 text-amber-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Owner</p>
                  <p className="text-xs text-gray-600">
                    Full access, can delete and transfer ownership
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <Shield className="w-4 h-4 text-blue-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Can edit</p>
                  <p className="text-xs text-gray-600">
                    Can view and send messages in the conversation
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <Eye className="w-4 h-4 text-gray-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">Can view</p>
                  <p className="text-xs text-gray-600">
                    Can only view the conversation, cannot edit
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Backend Pending Notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                <span className="text-amber-600 text-sm font-semibold">!</span>
              </div>
            </div>
            <div>
              <p className="text-sm font-medium text-amber-900">
                Backend Integration Pending
              </p>
              <p className="text-xs text-amber-700 mt-1">
                User collaboration features will be available once the backend API
                is implemented.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { Eye, EyeOff, LogIn, User, Shield } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

// Import types from AuthContext
type UserRole = "admin" | "user";

interface User {
  id: string;
  username: string;
  role: UserRole;
  name: string;
}

export default function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // Use API login
      await login(username, password);
      setLoading(false);
    } catch (error: any) {
      setError(error.message || "Login failed. Please try again.");
      setLoading(false);
      // Don't reset password visibility on error
    }
  };

  

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-black rounded-full flex items-center justify-center mb-4">
            <Shield className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">
            Thai Text Segmenter
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in to access the segmentation system
          </p>
        </div>

        {/* Login Form */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <form className="space-y-6" onSubmit={handleLogin}>
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none relative block w-full pl-10 pr-3 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-black focus:z-10 sm:text-sm"
                  placeholder="Enter your username"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <LogIn className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none relative block w-full pl-10 pr-10 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-black focus:z-10 sm:text-sm"
                  placeholder="Enter your password"
                />
                 <button
                   type="button"
                   className="absolute inset-y-0 right-0 pr-3 flex items-center z-20 hover:bg-gray-100 rounded-r-lg"
                   onClick={() => {
                     console.log('Eye icon clicked, current state:', showPassword);
                     setShowPassword(!showPassword);
                   }}
                   style={{ cursor: 'pointer' }}
                   title={showPassword ? "Hide password" : "Show password"}
                 >
                   {showPassword ? (
                     <EyeOff className="h-4 w-4 text-gray-400 hover:text-gray-600 transition-colors" />
                   ) : (
                     <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600 transition-colors" />
                   )}
                 </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Signing in...
                  </div>
                ) : (
                  "Sign in"
                )}
              </button>
             </div>
           </form>


        </div>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            Made by Eunice Leow • Thai Text Segmentation System
          </p>
        </div>
      </div>
    </div>
  );
}
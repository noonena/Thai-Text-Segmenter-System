

// import { useState, useEffect } from "react";
// import ProcessHtmlPage from "./pages/ProcessHtmlPage";
// import ProcessTextPage from "./pages/ProcessTextPage";
// import HistoryPage from "./pages/HistoryPage";
// import StatisticsPage from "./pages/StatisticsPage";
// import SettingPage from "./pages/SettingPage";
// import LoginPage from "./pages/LoginPage";
// import UserManagementPage from "./pages/UserManagementPage";
// import RoleManagementPage from "./pages/RoleManagementPage";
// import { Settings, FileText, History, ChartLine, LogOut, User, Users, Shield } from 'lucide-react';
// import { AuthProvider, useAuth, PERMISSIONS } from "./contexts/AuthContext";
// import { ProcessingProvider } from "./contexts/ProcessingContext";
// // import { apiClient } from "./services/api";
// import { ProcessingModal } from "./components/ProcessingModal";
// import { ApiErrorBoundary } from "./components/ApiErrorBoundary";

// type Page = "process" | "history" | "stats" | "users" | "roles";
// type InputMode = "html" | "text";
// type InputActive = "active" | "inactive";

// // Main app content with authentication
// function AppContent() {
//   const { user, logout, isAuthenticated, hasPermission } = useAuth();
//   const [page, setPage] = useState<Page>("process");
//   const [inputMode, setInputMode] = useState<InputMode>("html");
//   const [inputActive, setInputActive] = useState<InputActive>("active");
//   const [open, setOpen] = useState(false);
//   const [settings, setSettings] = useState({
//     tag: "span" as "span" | "div",
//     cssClass: ""
//   });
//   const [apiInitialized, setApiInitialized] = useState(false);

//   // Initialize API client on mount
//   useEffect(() => {
//     const initializeApi = async () => {
//       try {
//         await apiClient.initialize();
//         setApiInitialized(true);
//         console.log('🚀 API client initialized successfully');
//       } catch (error) {
//         console.error('❌ Failed to initialize API client:', error);
//         setApiInitialized(true); // Continue even if initialization fails
//       }
//     };

//     initializeApi();
//   }, []);

//   if (!apiInitialized) {
//     return (
//       <div className="h-screen flex items-center justify-center">
//         <div className="text-center">
//           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
//           <p>Initializing API connections...</p>
//         </div>
//       </div>
//     );
//   }

//   const handleApplySettings = (newSettings: { tag: "span" | "div"; cssClass: string }) => {
//     setSettings(newSettings);
//     console.log("Applied settings:", newSettings);
//   };

//   // If not authenticated, show login page
//   if (!isAuthenticated) {
//     return <LoginPage />;
//   }

// return (
//     <div>
//       <div className="h-screen">
//         <div className="max-w-[95%] mx-auto pt-[2.5%] flex flex-col h-full">
//           <div className="h-[12vh] bg-white rounded-lg shadow-md px-8 py-4 flex items-center justify-between">
//             <div className="flex flex-col gap-2">
//               <h1 className="text-2xl font-semibold">Thai text segmenter</h1>
//               <div className="flex items-center gap-4">
//                 <p className="text-sm text-gray-400">Made by Eunice Leow</p>
//                 {user && (
//                   <div className="flex items-center gap-2">
//                     <div className={`px-2 py-1 rounded-full text-xs font-medium ${
//                       user.role === 'admin' ? 'bg-red-100 text-red-700' :
//                       user.role === 'user' ? 'bg-blue-100 text-blue-700' :
//                       'bg-green-100 text-green-700'
//                     }`}>
//                       {user.role.toUpperCase()}
//                     </div>
//                     <span className="text-sm text-gray-600">Welcome, {user.name}</span>
//                   </div>
//                 )}
//               </div>
//             </div>
//             <div className="flex items-center gap-4">
//               {/* Settings button - only for admin */}
//               {hasPermission(PERMISSIONS.ACCESS_SETTINGS) && (
//                 <button onClick={() => setOpen(true)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
//                   <Settings className="w-6 h-6" />
//                 </button>
//               )}
              
//               {/* User menu */}
//               <div className="flex items-center gap-2">
//                 <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
//                   <User className="w-4 h-4 text-gray-600" />
//                   <span className="text-sm text-gray-700">{user?.username}</span>
//                 </div>
//                 <button 
//                   onClick={logout}
//                   className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
//                   title="Logout"
//                 >
//                   <LogOut className="w-5 h-5 text-gray-600" />
//                 </button>
//               </div>
//             </div>
//             {open && (
//               <SettingPage 
//                 onClose={() => setOpen(false)}
//                 onApply={handleApplySettings}
//               />
//             )}
//           </div>

//           <div className="h-full pt-[2%] flex-1">
//             <div className="h-full bg-white rounded-t-lg shadow-md flex flex-col">
// <div className="w-full flex flex-col bg-(--light-grayish) rounded-t-lg sm:flex-row justify-between py-0 sm:h-[50px]">
//                 <div className="flex w-full justify-between sm:justify-start h-full flex-1">
//                   {/* Process tab - Available to admin and user */}
//                   {hasPermission(PERMISSIONS.PROCESS_TEXT) && (
//                     <button
//                       onClick={() => {
//                         setPage("process");
//                         setInputActive("active");
//                       }}
//                       className={
//                         "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
//                         (page === "process"
//                           ? "bg-black text-white"
//                           : "bg-transparent text-black")
//                       }
//                     >
//                       <span className="flex items-center gap-2">
//                         <FileText className="w-4 h-4" />
//                         <span>Process</span>
//                       </span>
//                     </button>
//                   )}
                  
//                   {/* History tab - Available to admin, user */}
//                   {hasPermission(PERMISSIONS.VIEW_HISTORY) && (
//                     <button
//                       onClick={() => {
//                         setPage("history");
//                         setInputActive("inactive");
//                       }}
//                       className={
//                         "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
//                         (page === "history"
//                           ? "bg-black text-white"
//                           : "bg-transparent text-black")
//                       }
//                     >
//                       <span className="flex items-center gap-2">
//                         <History className="w-4 h-4" />
//                         <span>History</span>
//                       </span>
//                     </button>
//                   )}
                  
//                    {/* Statistics tab - Available to admin*/}
//                    {hasPermission(PERMISSIONS.VIEW_STATISTICS) && (
//                      <button
//                        onClick={() => {
//                          setPage("stats");
//                          setInputActive("inactive");
//                        }}
//                        className={
//                          "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
//                          (page === "stats"
//                            ? "bg-black text-white"
//                            : "bg-transparent text-black")
//                        }
//                      >
//                        <span className="flex items-center gap-2">
//                          <ChartLine className="w-4 h-4" />
//                          <span>Statistics</span>
//                        </span>
//                      </button>
//                    )}
                   
//                    {/* User Management tab - Available to admin only */}
//                    {hasPermission(PERMISSIONS.MANAGE_USERS) && (
//                      <button
//                        onClick={() => {
//                          setPage("users");
//                          setInputActive("inactive");
//                        }}
//                        className={
//                          "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
//                          (page === "users"
//                            ? "bg-black text-white"
//                            : "bg-transparent text-black")
//                        }
//                      >
//                        <span className="flex items-center gap-2">
//                          <Users className="w-4 h-4" />
//                          <span>Users</span>
//                        </span>
//                      </button>
//                    )}
                   
//                    {/* Role Management tab - Available to admin only */}
//                    {hasPermission(PERMISSIONS.MANAGE_USERS) && (
//                      <button
//                        onClick={() => {
//                          setPage("roles");
//                          setInputActive("inactive");
//                        }}
//                        className={
//                          "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
//                          (page === "roles"
//                            ? "bg-black text-white"
//                            : "bg-transparent text-black")
//                        }
//                      >
//                        <span className="flex items-center gap-2">
//                          <Shield className="w-4 h-4" />
//                          <span>Roles</span>
//                        </span>
//                      </button>
//                    )}
//                 </div>
//                 {inputActive === "active" && (
//                   <div className="flex w-full sm:w-[15%] h-9 sm:h-full rounded-lg border-2 border-black mt-1 sm:mt-0">
//                     <button
//                       onClick={() => setInputMode("html")}
//                       className={
//                         "flex-1 text-center " +
//                         (inputMode === "html"
//                           ? "bg-black text-white rounded-r-lg rounded-l-sm"
//                           : "bg-transparent text-black")
//                       }
//                     >
//                       HTML
//                     </button>
//                     <button
//                       onClick={() => setInputMode("text")}
//                       className={
//                         "flex-1 text-center " +
//                         (inputMode === "text"
//                           ? "bg-black text-white rounded-l-lg rounded-r-sm"
//                           : "bg-transparent text-black")
//                       }
//                     >
//                       Text
//                     </button>
//                   </div>
//                 )}
//                   </div>
//                  <div className="mt-4 flex-1 bg-white">
//                    <ApiErrorBoundary>
//                      {page === "process" && inputMode === "html" && (
//                        <ProcessHtmlPage settings={settings} />
//                      )}
//                      {page === "process" && inputMode === "text" && <ProcessTextPage settings={settings} />}
//                      {page === "history" && <HistoryPage />}
//                      {page === "stats" && <StatisticsPage />}
//                      {page === "users" && <UserManagementPage />}
//                      {page === "roles" && <RoleManagementPage />}
//                    </ApiErrorBoundary>
//                  </div>
//              </div>
//            </div>
//          </div>
//        </div>
//      </div>
//    );
//  }

// // Main App component with AuthProvider and ProcessingProvider
// function App() {
//   return (
//     <AuthProvider>
//       <ProcessingProvider>
//         <AppContent />
//         <ProcessingModal />
//       </ProcessingProvider>
//     </AuthProvider>
//   );
// }

// export default App;
import { useState } from "react";
import ProcessHtmlPage from "./pages/ProcessHtmlPage";
import ProcessTextPage from "./pages/ProcessTextPage";
import HistoryPage from "./pages/HistoryPage";
import StatisticsPage from "./pages/StatisticsPage";
import SettingPage from "./pages/SettingPage";
import LoginPage from "./pages/LoginPage";
import UserManagementPage from "./pages/UserManagementPage";
import RoleManagementPage from "./pages/RoleManagementPage";
import { Settings, FileText, History, ChartLine, LogOut, User, Users, Shield } from 'lucide-react';
import { AuthProvider, useAuth, PERMISSIONS } from "./contexts/AuthContext";
import { ProcessingProvider } from "./contexts/ProcessingContext";
import { ProcessingModal } from "./components/ProcessingModal";
import { ApiErrorBoundary } from "./components/ApiErrorBoundary";

type Page = "process" | "history" | "stats" | "users" | "roles";
type InputMode = "html" | "text";
type InputActive = "active" | "inactive";

// Main app content with authentication
function AppContent() {
  const { user, logout, isAuthenticated, hasPermission } = useAuth();
  const [page, setPage] = useState<Page>("process");
  const [inputMode, setInputMode] = useState<InputMode>("html");
  const [inputActive, setInputActive] = useState<InputActive>("active");
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState({
    tag: "span" as "span" | "div",
    cssClass: ""
  });

  const handleApplySettings = (newSettings: { tag: "span" | "div"; cssClass: string }) => {
    setSettings(newSettings);
    console.log("Applied settings:", newSettings);
  };

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return <LoginPage />;
  }

return (
    <div>
      <div className="h-screen">
        <div className="max-w-[95%] mx-auto pt-[2.5%] flex flex-col h-full">
          <div className="h-[12vh] bg-white rounded-lg shadow-md px-8 py-4 flex items-center justify-between">
            <div className="flex flex-col gap-2">
              <h1 className="text-2xl font-semibold">Thai text segmenter</h1>
              <div className="flex items-center gap-4">
                <p className="text-sm text-gray-400">Made by Eunice Leow</p>
                {user && (
                  <div className="flex items-center gap-2">
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.role === 'admin' ? 'bg-red-100 text-red-700' :
                      user.role === 'user' ? 'bg-blue-100 text-blue-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {user.role.toUpperCase()}
                    </div>
                    <span className="text-sm text-gray-600">Welcome, {user.name}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Settings button - only for admin */}
              {hasPermission(PERMISSIONS.ACCESS_SETTINGS) && (
                <button onClick={() => setOpen(true)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <Settings className="w-6 h-6" />
                </button>
              )}
              
              {/* User menu */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
                  <User className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-700">{user?.username}</span>
                </div>
                <button 
                  onClick={logout}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>
            {open && (
              <SettingPage 
                onClose={() => setOpen(false)}
                onApply={handleApplySettings}
              />
            )}
          </div>

          <div className="h-full pt-[2%] flex-1">
            <div className="h-full bg-white rounded-t-lg shadow-md flex flex-col">
<div className="w-full flex flex-col bg-(--light-grayish) rounded-t-lg sm:flex-row justify-between py-0 sm:h-[50px]">
                <div className="flex w-full justify-between sm:justify-start h-full flex-1">
                  {/* Process tab - Available to admin and user */}
                  {hasPermission(PERMISSIONS.PROCESS_TEXT) && (
                    <button
                      onClick={() => {
                        setPage("process");
                        setInputActive("active");
                      }}
                      className={
                        "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                        (page === "process"
                          ? "bg-black text-white"
                          : "bg-transparent text-black")
                      }
                    >
                      <span className="flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        <span>Process</span>
                      </span>
                    </button>
                  )}
                  
                  {/* History tab - Available to admin, user */}
                  {hasPermission(PERMISSIONS.VIEW_HISTORY) && (
                    <button
                      onClick={() => {
                        setPage("history");
                        setInputActive("inactive");
                      }}
                      className={
                        "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                        (page === "history"
                          ? "bg-black text-white"
                          : "bg-transparent text-black")
                      }
                    >
                      <span className="flex items-center gap-2">
                        <History className="w-4 h-4" />
                        <span>History</span>
                      </span>
                    </button>
                  )}
                  
                   {/* Statistics tab - Available to admin*/}
                   {hasPermission(PERMISSIONS.VIEW_STATISTICS) && (
                     <button
                       onClick={() => {
                         setPage("stats");
                         setInputActive("inactive");
                       }}
                       className={
                         "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                         (page === "stats"
                           ? "bg-black text-white"
                           : "bg-transparent text-black")
                       }
                     >
                       <span className="flex items-center gap-2">
                         <ChartLine className="w-4 h-4" />
                         <span>Statistics</span>
                       </span>
                     </button>
                   )}
                   
                   {/* User Management tab - Available to admin only */}
                   {hasPermission(PERMISSIONS.MANAGE_USERS) && (
                     <button
                       onClick={() => {
                         setPage("users");
                         setInputActive("inactive");
                       }}
                       className={
                         "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                         (page === "users"
                           ? "bg-black text-white"
                           : "bg-transparent text-black")
                       }
                     >
                       <span className="flex items-center gap-2">
                         <Users className="w-4 h-4" />
                         <span>Users</span>
                       </span>
                     </button>
                   )}
                   
                   {/* Role Management tab - Available to admin only */}
                   {hasPermission(PERMISSIONS.MANAGE_USERS) && (
                     <button
                       onClick={() => {
                         setPage("roles");
                         setInputActive("inactive");
                       }}
                       className={
                         "flex-1 sm:flex-0 px-4 sm:px-6 lg:px-10 py-2 rounded-t-lg " +
                         (page === "roles"
                           ? "bg-black text-white"
                           : "bg-transparent text-black")
                       }
                     >
                       <span className="flex items-center gap-2">
                         <Shield className="w-4 h-4" />
                         <span>Roles</span>
                       </span>
                     </button>
                   )}
                </div>
                {inputActive === "active" && (
                  <div className="flex w-full sm:w-[15%] h-9 sm:h-full rounded-lg border-2 border-black mt-1 sm:mt-0">
                    <button
                      onClick={() => setInputMode("html")}
                      className={
                        "flex-1 text-center " +
                        (inputMode === "html"
                          ? "bg-black text-white rounded-r-lg rounded-l-sm"
                          : "bg-transparent text-black")
                      }
                    >
                      HTML
                    </button>
                    <button
                      onClick={() => setInputMode("text")}
                      className={
                        "flex-1 text-center " +
                        (inputMode === "text"
                          ? "bg-black text-white rounded-l-lg rounded-r-sm"
                          : "bg-transparent text-black")
                      }
                    >
                      Text
                    </button>
                  </div>
                )}
                  </div>
                 <div className="mt-4 flex-1 bg-white">
                   <ApiErrorBoundary>
                     {page === "process" && inputMode === "html" && (
                       <ProcessHtmlPage settings={settings} />
                     )}
                     {page === "process" && inputMode === "text" && <ProcessTextPage settings={settings} />}
                     {page === "history" && <HistoryPage />}
                     {page === "stats" && <StatisticsPage />}
                     {page === "users" && <UserManagementPage />}
                     {page === "roles" && <RoleManagementPage />}
                   </ApiErrorBoundary>
                 </div>
             </div>
           </div>
         </div>
       </div>
     </div>
   );
 }

// Main App component with AuthProvider and ProcessingProvider
function App() {
  return (
    <AuthProvider>
      <ProcessingProvider>
        <AppContent />
        <ProcessingModal />
      </ProcessingProvider>
    </AuthProvider>
  );
}

export default App;
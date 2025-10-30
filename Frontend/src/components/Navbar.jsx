import { Link, useLocation } from "react-router-dom";
import { Home, BookOpen, CheckCircle, MessageCircle, FileText, GraduationCap } from "lucide-react";

export default function Navbar() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: "/", label: "Home", Icon: Home },
    { path: "/notes", label: "Notes", Icon: FileText },
    { path: "/learn", label: "Learn", Icon: BookOpen },
    { path: "/quiz", label: "Quiz", Icon: CheckCircle },
    { path: "/chat", label: "Chat", Icon: MessageCircle },
  ];

  return (
    <nav className="glass-effect border-b border-white/10 px-6 py-4 sticky top-0 z-50 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center group-hover:scale-110 transition-transform">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white group-hover:text-violet-300 transition-colors">
              Luma
            </h1>
            <p className="text-xs text-gray-400">AI-Powered Learning Platform</p>
          </div>
        </Link>
        <div className="flex gap-2">
          {navItems.map((item) => {
            const { Icon } = item;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-xl transition-all font-medium text-sm flex items-center gap-2 ${isActive(item.path)
                  ? 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/50'
                  : 'text-gray-300 hover:bg-white/10 hover:text-white'
                  }`}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden md:inline">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

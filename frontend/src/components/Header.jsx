import { Cpu, LogOut } from 'lucide-react';

export default function Header({ username, onLogout }) {
  return (
    <header className="bg-gray-900 border-b border-gray-800 px-4 lg:px-6 py-3 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-white font-semibold leading-tight">
            Verilog Testbench Generator
          </h1>
          <p className="text-xs text-gray-500 leading-tight">
            AI-Powered Automatic Testbench Generation
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-sm text-gray-300">{username}</span>
        </div>
        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white text-sm font-medium px-3 py-1.5 rounded-lg transition"
        >
          <LogOut className="w-4 h-4" />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
}

import { NavLink, Route, Routes } from "react-router-dom";
import { NewExtraction } from "./pages/NewExtraction";
import { JobsList } from "./pages/JobsList";
import { JobDetail } from "./pages/JobDetail";
import { RecordsList } from "./pages/RecordsList";
import { RecordDetail } from "./pages/RecordDetail";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-12">
          <h1 className="text-lg font-bold text-brand">Ashtronic RPA</h1>
          <nav className="flex gap-6 text-sm">
            <NavLink to="/" end className={navClass}>
              Nueva extracción
            </NavLink>
            <NavLink to="/jobs" className={navClass}>
              Jobs
            </NavLink>
            <NavLink to="/records" className={navClass}>
              Records
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-6xl px-4 py-8 flex-1 flex items-center justify-center">
          <Routes>
            <Route path="/" element={<NewExtraction />} />
            <Route path="/jobs" element={<JobsList />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/records" element={<RecordsList />} />
            <Route path="/records/:id" element={<RecordDetail />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function navClass({ isActive }: { isActive: boolean }): string {
  return isActive
    ? "rounded-md bg-gray-200 px-3 py-1.5 font-medium text-gray-900 transition-colors"
    : "rounded-md px-3 py-1.5 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900";
}

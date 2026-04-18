import { NavLink, Route, Routes } from "react-router-dom";
import { NewExtraction } from "./pages/NewExtraction";
import { JobsList } from "./pages/JobsList";
import { JobDetail } from "./pages/JobDetail";
import { RecordsList } from "./pages/RecordsList";

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-8">
          <h1 className="text-lg font-semibold text-brand">Ashtronic RPA</h1>
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

      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<NewExtraction />} />
            <Route path="/jobs" element={<JobsList />} />
            <Route path="/jobs/:id" element={<JobDetail />} />
            <Route path="/records" element={<RecordsList />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function navClass({ isActive }: { isActive: boolean }): string {
  return isActive
    ? "text-brand font-medium"
    : "text-gray-600 hover:text-gray-900";
}

import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useJobResults } from "@/hooks/useJobResults";
import { TopBar, Sidebar, type ViewKey } from "@/components/shell";
import LibraryView from "@/views/LibraryView";
import ManuscriptView from "@/views/ManuscriptView";
import TimelineView from "@/views/TimelineView";
import IssuesView from "@/views/IssuesView";
import CharactersView from "@/views/CharactersView";

export default function ResultsPage() {
  const { jobId = "" } = useParams<{ jobId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const viewParam = searchParams.get("view") as ViewKey | null;
  const view: ViewKey = viewParam ?? "manuscript";

  function setView(v: ViewKey) {
    if (v === "library") {
      navigate("/");
      return;
    }
    setSearchParams({ view: v });
  }

  const { job, chapters, timelineEvents, plotHoles, isLoading, error } = useJobResults(jobId);

  // Derive a nice title from the job filename if available
  const manuscriptTitle = jobId;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--ivy-bg)" }}>
        <p className="font-mono text-[12px] uppercase tracking-[0.2em]" style={{ color: "var(--ivy-inkFaint)" }}>
          Loading results…
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--ivy-bg)" }}>
        <div className="text-center">
          <p className="font-serif text-[20px] mb-2" style={{ color: "var(--ivy-inkDeep)" }}>
            Failed to load results
          </p>
          <p className="text-[13px] mb-4" style={{ color: "var(--ivy-inkMute)" }}>{error}</p>
          <button
            onClick={() => navigate("/")}
            className="font-mono text-[12px] px-4 py-2 rounded-sm"
            style={{ border: "1px solid var(--ivy-rule)", color: "var(--ivy-inkMute)" }}
          >
            ← Back to library
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: "var(--ivy-bg)" }}>
      <TopBar manuscriptTitle={manuscriptTitle} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar view={view} setView={setView} job={job} manuscriptTitle={manuscriptTitle} />

        <main className="flex-1 overflow-y-auto" style={{ background: "var(--ivy-bg)" }}>
          {view === "library" && <LibraryView />}
          {view === "manuscript" && (
            <ManuscriptView chapters={chapters} events={timelineEvents} />
          )}
          {view === "timeline" && (
            <TimelineView events={timelineEvents} />
          )}
          {view === "issues" && (
            <IssuesView holes={plotHoles} events={timelineEvents} />
          )}
          {view === "characters" && (
            <CharactersView events={timelineEvents} />
          )}
        </main>
      </div>
    </div>
  );
}

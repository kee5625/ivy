import { TopBar } from "@/components/shell";
import LibraryView from "@/views/LibraryView";

export default function HomePage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: "var(--ivy-bg)" }}>
      <TopBar />
      <main className="flex-1 overflow-y-auto">
        <LibraryView />
      </main>
    </div>
  );
}

import { useState } from "react";
import { TopBar } from "@/components/shell";
import { type PaletteKey } from "@/components/theme";
import LibraryView from "@/views/LibraryView";

export default function HomePage() {
  const [palette, setPalette] = useState<PaletteKey>("manuscript");

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: "var(--ivy-bg)" }}>
      <TopBar palette={palette} setPalette={setPalette} />
      <main className="flex-1 overflow-y-auto">
        <LibraryView />
      </main>
    </div>
  );
}

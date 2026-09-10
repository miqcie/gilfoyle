import { useMemo, useState } from "react";
import { MultiFileDiff } from "@pierre/diffs/react";
import { FileTree, useFileTree } from "@pierre/trees/react";
import { changedFiles, review } from "./fixture";
import { findingCountByPath } from "./review-model";
import "./styles.css";

const paths: string[] = changedFiles.map(({ path }) => path);
const gitStatus = paths.map((path) => ({ path, status: "modified" as const }));

export function App() {
  const counts = useMemo(() => findingCountByPath(review.findings), []);
  const [selectedPath, setSelectedPath] = useState<string>(paths[0]);
  const { model } = useFileTree({
    initialExpansion: "open",
    initialSelectedPaths: [paths[0]],
    paths,
    gitStatus,
    search: true,
    onSelectionChange: (selectedPaths) => {
      const selected = selectedPaths[selectedPaths.length - 1];
      if (typeof selected === "string" && paths.includes(selected)) {
        setSelectedPath(selected);
      }
    },
    renderRowDecoration: ({ item }) => counts[item.path]
      ? { text: `${counts[item.path]} finding${counts[item.path] === 1 ? "" : "s"}` }
      : null,
  });

  return <main>
    <header><h1>Gilfoyle review workbench</h1><p>{review.summary} Verdict: <strong>{review.verdict}</strong></p></header>
    <aside aria-label="Changed files">
      <FileTree model={model} header={<strong>Changed files · findings</strong>} style={{ height: 260 }} />
    </aside>
    <section aria-label="Annotated multi-file diff">
      <h2>Reviewing {selectedPath}</h2>
      {changedFiles.filter((file) => file.path === selectedPath).map((file) => <MultiFileDiff
        key={file.path}
        oldFile={{ name: file.path, contents: file.before }}
        newFile={{ name: file.path, contents: file.after }}
        options={{ diffStyle: "unified", theme: "github-dark", overflow: "wrap" }}
        lineAnnotations={review.findings.filter((finding) => finding.evidence.path === file.path).map((finding) => ({
          side: "additions" as const,
          lineNumber: finding.evidence.start_line,
          metadata: finding,
        }))}
        renderAnnotation={({ metadata }) => <article className={`finding ${metadata.severity}`}>
          <strong>{metadata.id} · {metadata.severity}</strong><br />{metadata.evidence.quote}
        </article>}
      />)}
    </section>
  </main>;
}

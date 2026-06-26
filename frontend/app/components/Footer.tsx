export default function Footer() {
  return (
    <footer className="border-t border-chroma-border py-12 mt-auto">
      <div className="max-w-5xl mx-auto px-6 flex flex-col items-center gap-2">
        <span className="font-medium text-sm text-chroma-fg tracking-tight">
          ExoVetter
        </span>
        <span className="text-xs text-chroma-muted-fg">
          BAH 2026 -- Challenge 7
        </span>
        <span className="text-xs text-chroma-muted-fg mt-2">
          &copy; {new Date().getFullYear()} ExoVetter. All rights reserved.
        </span>
      </div>
    </footer>
  );
}

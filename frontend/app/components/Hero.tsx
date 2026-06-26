"use client";

interface HeroProps {
  onUploadClick: () => void;
  onSampleClick: () => void;
}

export default function Hero({ onUploadClick, onSampleClick }: HeroProps) {
  return (
    <section className="w-full max-w-3xl mx-auto px-6 pt-16 pb-12">
      <h1 className="text-2xl font-normal text-chroma-fg tracking-tight">
        Upload. Analyze. Discover.
      </h1>
      <p className="mt-3 text-base text-chroma-muted-fg leading-relaxed">
        Drop a light curve and get instant transit analysis -- no sign-up
        required.
      </p>

      <div className="flex items-center gap-3 mt-8">
        <button
          onClick={onUploadClick}
          className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-4 py-2 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
        >
          Upload your data
        </button>
        <button
          onClick={onSampleClick}
          className="border border-chroma-border rounded-lg px-4 py-2 text-sm font-medium hover:bg-chroma-muted transition-colors cursor-pointer"
        >
          Try sample
        </button>
      </div>

      <div className="flex items-center gap-8 mt-8 pt-6 border-t border-chroma-border">
        {[
          { value: "3 Formats", caption: "CSV, JSON, NPZ" },
          { value: "200 MB", caption: "Max file size" },
          { value: "< 30s", caption: "Processing time" },
        ].map((stat) => (
          <div key={stat.value} className="flex flex-col gap-0.5">
            <span className="text-sm font-medium text-chroma-fg">
              {stat.value}
            </span>
            <span className="text-xs text-chroma-muted-fg">{stat.caption}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

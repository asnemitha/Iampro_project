export default function HeroBanner() {
  return (
    <div className="w-full bg-[#ebb23f] border-[2.5px] border-black rounded-2xl shadow-[6px_6px_0px_#000] p-6 sm:p-7 relative overflow-hidden transition-all">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
        
        {/* Left Content */}
        <div className="flex-1 max-w-3xl">
          {/* Badge */}
          <div className="inline-block bg-[#fbf7ee] text-neutral-900 border-2 border-black rounded-md px-2.5 py-1 mb-3.5 shadow-[1.5px_1.5px_0px_#000]">
            <span className="font-mono text-[11px] sm:text-xs font-bold tracking-wider uppercase">
              ACADEMIC VERIFICATION PIPELINE
            </span>
          </div>

          {/* Headline */}
          <h1 className="font-black text-2xl sm:text-3xl lg:text-[34px] text-[#3d1a04] tracking-tight leading-[1.15] mb-2.5 font-display">
            Did the model make that citation up?
          </h1>

          {/* Subtitle */}
          <p className="font-mono text-xs sm:text-[14px] text-[#2c1505] leading-relaxed font-medium">
            Multi-source DOI, author, and venue cross-referencing against Crossref, DataCite, Semantic Scholar, and OpenAlex.
          </p>
        </div>

        {/* Right Decorative Geometric Composition */}
        <div className="hidden sm:flex items-center gap-3 self-center md:self-auto shrink-0 select-none">
          {/* Red Circle */}
          <div className="w-9 h-9 rounded-full bg-[#e04f43] border-2 border-black shadow-[2px_2px_0px_#000]" />

          {/* Yellow Tilted Square */}
          <div className="w-8 h-8 rounded-md bg-[#f5b731] border-2 border-black shadow-[2px_2px_0px_#000] rotate-12 transform" />

          {/* Blue Rounded Square */}
          <div className="w-9 h-9 rounded-xl bg-[#2563eb] border-2 border-black shadow-[2px_2px_0px_#000]" />

          {/* Dotted Grid Pattern */}
          <div className="grid grid-cols-4 gap-1.5 pl-1.5">
            {[...Array(12)].map((_, i) => (
              <span 
                key={i} 
                className="w-1.5 h-1.5 rounded-full bg-neutral-800" 
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

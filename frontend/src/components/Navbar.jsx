import { useState } from "react";

export default function Navbar({ activeTab, setActiveTab, theme, toggleTheme }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: "verify", label: "VERIFY" },
    { id: "benchmark", label: "BENCHMARK" },
    { id: "how-it-works", label: "HOW IT WORKS" },
    { id: "about", label: "ABOUT" },
  ];

  const handleTabClick = (id) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <nav className="w-full bg-[#fbf7ee] dark:bg-[#18181b] border-b-[2.5px] border-black transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logo & Brand Wordmark */}
          <div 
            className="flex items-center gap-3.5 cursor-pointer select-none"
            onClick={() => handleTabClick("verify")}
            title="CitationGuard Home"
          >
            {/* Shield Logo Icon */}
            <div className="w-10 h-10 rounded-xl bg-[#f5b731] border-2 border-black shadow-[2.5px_2.5px_0px_#000] flex items-center justify-center shrink-0">
              <svg 
                className="w-6 h-6" 
                viewBox="0 0 24 24" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
              >
                {/* Shield Body */}
                <path 
                  d="M12 2L4 5V11.5C4 16.5 7.4 21.1 12 22C16.6 21.1 20 16.5 20 11.5V5L12 2Z" 
                  fill="#2563eb" 
                  stroke="#000000" 
                  strokeWidth="1.75" 
                  strokeLinejoin="round"
                />
                {/* Upward Chevron / Arrow */}
                <path 
                  d="M12 7.5L8.5 12H10.5V15.5H13.5V12H15.5L12 7.5Z" 
                  fill="#ffffff" 
                  stroke="#000000" 
                  strokeWidth="1.2"
                />
              </svg>
            </div>

            {/* Wordmark & Subtitle */}
            <div className="flex flex-col">
              <span className="font-extrabold text-[22px] tracking-tight leading-none text-neutral-900 dark:text-neutral-100 font-display">
                CitationGuard
              </span>
              <span className="font-mono text-[10px] font-bold tracking-[0.16em] text-neutral-600 dark:text-neutral-400 uppercase mt-1">
                CITATION VERIFICATION
              </span>
            </div>
          </div>

          {/* Desktop Navigation Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-[13px] font-extrabold tracking-wider transition-all cursor-pointer font-mono ${
                    isActive
                      ? "nav-btn-active"
                      : "bg-white dark:bg-[#27272a] text-neutral-900 dark:text-neutral-100 border-2 border-black shadow-btn"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}

            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              className={`w-10 h-10 rounded-xl border-2 border-black shadow-btn flex items-center justify-center cursor-pointer transition-all ml-1 ${
                theme === "dark" ? "bg-[#27272a]" : "bg-white"
              }`}
              aria-label={theme === "dark" ? "Current theme: Dark. Click to switch to Light mode" : "Current theme: Light. Click to switch to Dark mode"}
              title={theme === "dark" ? "Dark mode active (click for Light)" : "Light mode active (click for Dark)"}
            >
              {theme === "dark" ? (
                /* Dark Mode: clearly visible yellow moon icon */
                <svg 
                  className="w-5 h-5 text-[#f5b731] fill-[#f5b731] stroke-black stroke-[1.2]" 
                  viewBox="0 0 24 24"
                >
                  <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              ) : (
                /* Light Mode: clearly visible yellow sun icon */
                <svg 
                  className="w-5 h-5 text-[#f5b731] fill-[#f5b731] stroke-black stroke-[1.2]" 
                  viewBox="0 0 24 24"
                >
                  <circle cx="12" cy="12" r="4" />
                  <path strokeLinecap="round" strokeWidth="2" stroke="#f5b731" d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M6.34 17.66l-1.41 1.41m14.14-14.14l-1.41 1.41" />
                </svg>
              )}
            </button>
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className={`w-9 h-9 rounded-lg border-2 border-black shadow-[2px_2px_0px_#000] flex items-center justify-center cursor-pointer ${
                theme === "dark" ? "bg-[#27272a]" : "bg-white"
              }`}
              aria-label={theme === "dark" ? "Current theme: Dark. Click to switch to Light mode" : "Current theme: Light. Click to switch to Dark mode"}
            >
              {theme === "dark" ? (
                <span className="text-base select-none" role="img" aria-label="Dark mode">🌙</span>
              ) : (
                <span className="text-base select-none text-[#f5b731]" role="img" aria-label="Light mode">☀️</span>
              )}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg bg-white dark:bg-[#27272a] border-2 border-black shadow-[2px_2px_0px_#000] text-black dark:text-white"
              aria-label="Toggle Navigation Menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>

        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t-2 border-black space-y-2">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`w-full text-left px-4 py-2.5 rounded-xl font-mono text-sm font-bold tracking-wider border-2 border-black shadow-[2px_2px_0px_#000] ${
                    isActive
                      ? "bg-[#f5b731] text-black font-extrabold"
                      : "bg-white dark:bg-[#27272a] text-black dark:text-white"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        )}

      </div>
    </nav>
  );
}

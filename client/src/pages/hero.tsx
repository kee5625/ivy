// HeroSection.jsx
import { useRef } from "react";

const ArrowIcon = () => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 28,
      height: 28,
      borderRadius: "50%",
      background: "#fff",
      marginLeft: 8,
      flexShrink: 0,
    }}
  >
    <svg
      width="13"
      height="13"
      viewBox="0 0 13 13"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M2.5 10.5L10.5 2.5M10.5 2.5H4.5M10.5 2.5V8.5"
        stroke="#222"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  </span>
);

const PlayIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 18 18"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{ marginRight: 8, flexShrink: 0 }}
  >
    <circle cx="9" cy="9" r="9" fill="#222" />
    <polygon points="7,5.5 13.5,9 7,12.5" fill="#fff" />
  </svg>
);

const LogoisumLogo = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
    <div
      style={{
        width: 32,
        height: 32,
        borderRadius: 8,
        background: "#222",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <rect x="2" y="2" width="6" height="6" rx="1.5" fill="#fff" />
        <rect x="10" y="2" width="6" height="6" rx="1.5" fill="#fff" opacity="0.5" />
        <rect x="2" y="10" width="6" height="6" rx="1.5" fill="#fff" opacity="0.5" />
        <rect x="10" y="10" width="6" height="6" rx="1.5" fill="#fff" />
      </svg>
    </div>
    <span
      style={{
        fontFamily: "'Barlow', sans-serif",
        fontWeight: 700,
        fontSize: 20,
        color: "#222",
        letterSpacing: "-0.5px",
      }}
    >
      Logoisum
    </span>
  </div>
);

export default function Hero() {
  const videoRef = useRef(null);

  return (
    <>
      {/* Google Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Instrument+Serif:ital@0;1&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .hero-section {
          position: relative;
          width: 100%;
          min-height: 90vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          font-family: 'Barlow', sans-serif;
        }

        /* ── Video Background ── */
        .hero-video {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
          z-index: 0;
        }

        /* ── Navbar ── */
        .navbar {
          position: relative;
          z-index: 10;
          margin: 20px 24px 0;
          background: rgba(255,255,255,0.96);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border-radius: 16px;
          box-shadow: 0 4px 32px rgba(0,0,0,0.10), 0 1px 4px rgba(0,0,0,0.06);
          padding: 12px 28px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }

        .nav-links {
          display: flex;
          align-items: center;
          gap: 32px;
          list-style: none;
        }

        .nav-links a {
          font-family: 'Barlow', sans-serif;
          font-weight: 500;
          font-size: 14px;
          color: #333;
          text-decoration: none;
          letter-spacing: 0.01em;
          transition: color 0.2s;
        }

        .nav-links a:hover { color: #000; }

        .cta-btn {
          display: inline-flex;
          align-items: center;
          background: #222;
          color: #fff;
          border: none;
          border-radius: 100px;
          padding: 9px 16px 9px 20px;
          font-family: 'Barlow', sans-serif;
          font-weight: 600;
          font-size: 14px;
          cursor: pointer;
          letter-spacing: 0.01em;
          transition: background 0.2s, transform 0.15s;
          white-space: nowrap;
        }

        .cta-btn:hover { background: #111; transform: translateY(-1px); }

        /* ── Hero Content ── */
        .hero-content {
          position: relative;
          z-index: 10;
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 60px 24px 80px;
          gap: 0;
        }

        .hero-tag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(255,255,255,0.18);
          border: 1px solid rgba(255,255,255,0.35);
          backdrop-filter: blur(8px);
          border-radius: 100px;
          padding: 6px 14px;
          font-family: 'Barlow', sans-serif;
          font-weight: 500;
          font-size: 13px;
          color: #fff;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          margin-bottom: 28px;
        }

        .hero-tag-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #fff;
          opacity: 0.8;
        }

        .headline-line1 {
          font-family: 'Barlow', sans-serif;
          font-weight: 600;
          font-size: clamp(28px, 4.5vw, 52px);
          color: #fff;
          letter-spacing: -4px;
          line-height: 1.05;
          display: block;
          margin-bottom: 4px;
        }

        .headline-line2 {
          font-family: 'Instrument Serif', serif;
          font-style: italic;
          font-size: clamp(52px, 7.5vw, 84px);
          color: #fff;
          line-height: 1.0;
          letter-spacing: -2px;
          display: block;
          margin-bottom: 28px;
        }

        .hero-subtext {
          font-family: 'Barlow', sans-serif;
          font-weight: 500;
          font-size: 18px;
          color: rgba(255,255,255,0.82);
          letter-spacing: 0.01em;
          margin-bottom: 40px;
          max-width: 480px;
          line-height: 1.6;
        }

        .workreel-btn {
          display: inline-flex;
          align-items: center;
          background: #fff;
          color: #222;
          border: none;
          border-radius: 100px;
          padding: 14px 28px;
          font-family: 'Barlow', sans-serif;
          font-weight: 600;
          font-size: 16px;
          cursor: pointer;
          letter-spacing: 0.01em;
          box-shadow: 0 8px 32px rgba(0,0,0,0.18);
          transition: transform 0.18s, box-shadow 0.18s;
        }

        .workreel-btn:hover {
          transform: translateY(-2px) scale(1.02);
          box-shadow: 0 14px 40px rgba(0,0,0,0.22);
        }

        /* ── Responsive ── */
        @media (max-width: 768px) {
          .navbar { margin: 12px 12px 0; padding: 10px 16px; }
          .nav-links { gap: 18px; }
          .nav-links a { font-size: 13px; }
          .headline-line1 { letter-spacing: -2px; }
          .headline-line2 { letter-spacing: -1px; }
          .hero-subtext { font-size: 15px; }
        }

        @media (max-width: 540px) {
          .nav-links { display: none; }
          .cta-btn span.cta-label { display: none; }
        }
      `}</style>

      <section className="hero-section">
        {/* ── Video Background ── */}
        <video
          ref={videoRef}
          className="hero-video"
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260228_065522_522e2295-ba22-457e-8fdb-fbcd68109c73.mp4"
          autoPlay
          muted
          loop
          playsInline
        />

        {/* ── Floating Navbar ── */}
        <nav className="navbar">
          <LogoisumLogo />

          <ul className="nav-links">
            {["About", "Works", "Services", "Testimonial"].map((item) => (
              <li key={item}>
                <a href={`#${item.toLowerCase()}`}>{item}</a>
              </li>
            ))}
          </ul>

          <button className="cta-btn">
            <span className="cta-label">Book A Free Meeting</span>
            <ArrowIcon />
          </button>
        </nav>

        {/* ── Hero Content ── */}
        <div className="hero-content">
          <div className="hero-tag">
            <span className="hero-tag-dot" />
            Premium Video Editing Agency
          </div>

          <h1 style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <span className="headline-line1">Agency that makes your</span>
            <span className="headline-line2">videos &amp; reels viral</span>
          </h1>

          <p className="hero-subtext">
            Short-form video editing for Influencers, Creators and Brands
          </p>

          <button className="workreel-btn">
            <PlayIcon />
            See Our Workreel
          </button>
        </div>
      </section>
    </>
  );
}

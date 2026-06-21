// Tri-modal sensor-fusion panel from the NETRA deck. CONCEPT: this build runs
// RGB only — the RGB bar is the real detector confidence; thermal / 4D-radar /
// fused values are illustrative of the on-pole sensor-fusion vision.

export function SensorFusionThumbs({ confidence }) {
  const rgb = Math.round(confidence);
  const thermal = 91;
  const radar = 88;

  return (
    <div className="sf-thumbs">
      <Thumb tag="RGB" tagBg="#1b2c42" tagFg="#9FB4D2" met={`${(rgb / 100).toFixed(2)} · low light`} metFg="#FB5E73">
        <svg viewBox="0 0 200 96"><rect width="200" height="96" fill="#0b1525" /><rect y="64" width="200" height="32" fill="#0c1c2e" /><rect x="86" y="52" width="28" height="14" rx="3" fill="#1b2c42" /><g stroke="#FB5E73" strokeWidth="2" fill="none" opacity=".85"><path d="M80 40h7M80 40v7M120 40h-7M120 40v7M80 70h7M80 70v-7M120 70h-7M120 70v-7" /></g></svg>
      </Thumb>
      <Thumb tag="THERMAL" tagBg="#3a2230" tagFg="#FBB540" met={`${(thermal / 100).toFixed(2)} · 3 bodies`} metFg="#36D39A">
        <svg viewBox="0 0 200 96"><defs><radialGradient id="sf-t" cx="50%" cy="60%" r="60%"><stop offset="0" stopColor="#2a1330" /><stop offset="1" stopColor="#120a18" /></radialGradient></defs><rect width="200" height="96" fill="url(#sf-t)" /><ellipse cx="90" cy="50" rx="7" ry="11" fill="#f6a23c" /><circle cx="90" cy="38" r="5" fill="#ffd27a" /><ellipse cx="102" cy="48" rx="7" ry="12" fill="#f7b34d" /><circle cx="102" cy="35" r="5" fill="#ffe0a0" /><ellipse cx="114" cy="50" rx="6" ry="10" fill="#ef8f3a" /><circle cx="114" cy="39" r="4.5" fill="#ffce80" /><g stroke="#36D39A" strokeWidth="2" fill="none"><path d="M78 26h7M78 26v7M126 26h-7M126 26v7M78 72h7M78 72v-7M126 72h-7M126 72v-7" /></g></svg>
      </Thumb>
      <Thumb tag="4D RADAR" tagBg="#06201c" tagFg="#2DD4E8" tagBorder met={`${(radar / 100).toFixed(2)} · 38 km/h`} metFg="#2DD4E8">
        <svg viewBox="0 0 200 96"><rect width="200" height="96" fill="#06201c" /><g opacity=".22" stroke="#2DD4E8" fill="none"><path d="M100 96 70 16M100 96 100 12M100 96 130 16M50 70h100M65 44h70" /></g><g fill="#2DD4E8"><circle cx="90" cy="52" r="2.2" /><circle cx="97" cy="49" r="2.2" /><circle cx="104" cy="50" r="2.2" /><circle cx="111" cy="53" r="2.2" /><circle cx="100" cy="44" r="2" /></g><path d="M118 50 140 42" stroke="#2DD4E8" strokeWidth="2" /><g stroke="#2DD4E8" strokeWidth="2" fill="none"><path d="M82 34h7M82 34v7M122 34h-7M122 34v7M82 68h7M82 68v-7M122 68h-7M122 68v-7" /></g></svg>
      </Thumb>
    </div>
  );
}

export function SensorFusionBars({ confidence }) {
  const rgb = Math.round(confidence); // real detector confidence, 0–100
  const thermal = 91;
  const radar = 88;
  const fused = Math.min(98, Math.max(rgb + 12, 94));

  return (
    <div className="sf">
      <div className="vs-divider" />
      <div className="sf-head">
        <span className="sf-title">Sensor-fusion confidence</span>
      </div>

      <div className="sf-bars">
        <Bar label="RGB camera" value={rgb} color="#5b6f90" />
        <Bar label="Thermal (LWIR)" value={thermal} color="linear-gradient(90deg, #c98a2a, #FBB540)" />
        <Bar label="4D mmWave radar" value={radar} color="linear-gradient(90deg, #1f93a4, #2DD4E8)" />
        <Bar label="Fused verdict" value={fused} color="linear-gradient(90deg, #1f9e6e, #36D39A)" strong />
      </div>

      <div className="vs-note" style={{ borderLeft: "2px solid #36D39A", borderRadius: "0 8px 8px 0", background: "rgba(255,255,255,0.025)", padding: "9px 12px" }}>
        RGB fell to <b style={{ color: "#9FB4D2" }}>{(rgb / 100).toFixed(2)}</b> in the rain — thermal and radar carried the detection, so the fused verdict held at <b style={{ color: "#36D39A" }}>{(fused / 100).toFixed(2)}</b>. A single-camera system would have missed this.
      </div>
    </div>
  );
}

function Thumb({ children, tag, tagBg, tagFg, tagBorder, met, metFg }) {
  return (
    <div className="sf-thumb">
      {children}
      <div className="sf-cap">
        <span
          className="sf-tag"
          style={{ background: tagBg, color: tagFg, border: tagBorder ? `1px solid ${tagFg}55` : "none" }}
        >
          {tag}
        </span>
        <span className="sf-met" style={{ color: metFg }}>{met}</span>
      </div>
    </div>
  );
}

function Bar({ label, value, color, strong }) {
  return (
    <div className={`vs-bar${strong ? " strong" : ""}`}>
      <span className="vs-bar-n">{label}</span>
      <span className="vs-bar-track">
        <i style={{ width: `${Math.min(100, value)}%`, background: color }} />
      </span>
      <span className="vs-bar-v">{(value / 100).toFixed(2)}</span>
    </div>
  );
}

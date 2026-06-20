import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#0f766e", "#b3432d", "#9a6a1c", "#3f6f8f", "#6b5b95"];

export default function Donut({ data, total }) {
  return (
    <div className="donut">
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={62}
            outerRadius={90}
            paddingAngle={2}
            stroke="none"
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              borderRadius: 10,
              border: "1px solid var(--border)",
              fontSize: 13,
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="donut-center">
        <span className="donut-total">{total}</span>
        <span className="donut-label">total</span>
      </div>
    </div>
  );
}

export { COLORS };

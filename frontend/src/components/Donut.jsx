import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#3B9EFF", "#FB5E73", "#FBB540", "#2DD4E8", "#A78BFA", "#36D39A"];

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
              background: "#0c1827",
              borderRadius: 10,
              border: "1px solid rgba(132,168,222,0.2)",
              fontSize: 13,
            }}
            itemStyle={{ color: "#EAF1FB" }}
            labelStyle={{ color: "#9FB4D2" }}
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

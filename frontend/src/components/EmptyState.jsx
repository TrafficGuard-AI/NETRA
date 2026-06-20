export default function EmptyState({ icon: Icon, title, hint }) {
  return (
    <div className="empty-state">
      {Icon && (
        <span className="empty-icon">
          <Icon size={22} strokeWidth={1.5} />
        </span>
      )}
      <p className="empty-title">{title}</p>
      {hint && <span className="empty-hint">{hint}</span>}
    </div>
  );
}

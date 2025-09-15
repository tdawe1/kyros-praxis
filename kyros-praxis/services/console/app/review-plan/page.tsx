import fs from 'fs';
import { repoFile } from '@/lib/server/repoRoot';

export default function ReviewPlanPage() {
  let content = 'No review plan found.';
  try {
    const file = repoFile('docs', 'review-plan.md');
    if (fs.existsSync(file)) {
      content = fs.readFileSync(file, 'utf8');
    }
  } catch (e) {
    content = 'Failed to load review plan.';
  }
  return (
    <div className="cds--grid">
      <div className="cds--row">
        <div className="cds--col-lg-12">
          <h2>Review Plan</h2>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{content}</pre>
        </div>
      </div>
    </div>
  );
}

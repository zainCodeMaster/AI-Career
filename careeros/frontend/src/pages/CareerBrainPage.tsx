import { FormEvent, useState } from 'react';
import { CareerBrainApi, type CareerBrainSearchResult } from '../api/careerBrain';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';

export function CareerBrainPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CareerBrainSearchResult[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [context, setContext] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [indexing, setIndexing] = useState(false);

  const search = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setMessage(null);
    try {
      const response = await CareerBrainApi.search(query.trim());
      setResults(response.results);
      if (response.results.length === 0) setMessage('No matching career information was found.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const rebuildIndex = async () => {
    setIndexing(true);
    setError(null);
    setMessage(null);
    try {
      const response = await CareerBrainApi.index();
      setMessage(`${response.documents_processed} documents indexed with ${response.chunks_created} searchable sections.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Indexing failed');
    } finally {
      setIndexing(false);
    }
  };

  const buildContext = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setMessage(null);
    try {
      const response = await CareerBrainApi.context(query.trim());
      setContext(response.context);
      setResults(response.results);
      setMessage('Career context retrieved from your indexed data.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Context retrieval failed');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title="Career Brain"
        description="Search your resumes, profile, and career history from one place."
        action={<Button onClick={rebuildIndex} disabled={indexing}>{indexing ? 'Indexing...' : 'Refresh knowledge'}</Button>}
      />
      <Card className="mb-5">
        <form onSubmit={search} className="flex flex-col gap-3 sm:flex-row">
          <Input aria-label="Career Brain search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about your skills, experience, or goals" />
          <div className="flex gap-2">
            <Button type="submit" disabled={searching || !query.trim()}>{searching ? 'Searching...' : 'Search'}</Button>
            <Button type="button" variant="secondary" onClick={() => void buildContext()} disabled={searching || !query.trim()}>Build context</Button>
          </div>
        </form>
      </Card>
      {error && <ErrorState message={error} onRetry={() => void search(new Event('submit') as unknown as FormEvent)} className="mb-5" />}
      {message && <p className="mb-5 rounded-md border border-primary-light bg-primary-light p-3 text-body-sm text-primary-dark" role="status">{message}</p>}
      {context && (
        <Card className="mb-5">
          <h2 className="text-h3 text-neutral-900">Retrieved career context</h2>
          <pre className="mt-3 whitespace-pre-wrap text-body text-neutral-700">{context}</pre>
        </Card>
      )}
      <div className="space-y-3">
        {results.map((result) => (
          <Card key={result.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-h3 text-neutral-900">{result.title || result.source_type}</h2>
                <p className="mt-2 whitespace-pre-line text-body text-neutral-700">{result.content}</p>
              </div>
              <span className="shrink-0 text-caption text-neutral-500">{Math.round(result.score * 100)}%</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

import { FormEvent, useState } from 'react';
import { CareerBrainApi, type CareerBrainSearchResult, type CareerBrainAnswerResponse, type CareerBrainAnswerSource } from '../api/careerBrain';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ErrorState } from '../components/ui/ErrorState';
import { Input } from '../components/ui/Input';
import { PageHeader } from '../components/layout/PageHeader';
import { Badge } from '../components/ui/Badge';

export function CareerBrainPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CareerBrainSearchResult[]>([]);
  const [answer, setAnswer] = useState<string | null>(null);
  const [answerSources, setAnswerSources] = useState<CareerBrainAnswerSource[]>([]);
  const [context, setContext] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [modelInfo, setModelInfo] = useState<{ model: string; confidence: string } | null>(null);

  const search = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setMessage(null);
    setAnswer(null);
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

  const ask = async () => {
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    setMessage(null);
    setAnswer(null);
    try {
      const response: CareerBrainAnswerResponse = await CareerBrainApi.answer(query.trim());
      setAnswer(response.answer);
      setAnswerSources(response.sources);
      setModelInfo({ model: response.model, confidence: response.confidence });
      if (response.warning) setMessage(response.warning);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Answer generation failed');
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

  const confidenceBadge = (confidence?: string) => {
    if (!confidence) return <Badge variant="neutral">N/A</Badge>;
    const variant = confidence === 'high' ? 'success' : confidence === 'medium' ? 'warning' : 'error';
    return <Badge variant={variant}>{confidence}</Badge>;
  };

  return (
    <div className="mx-auto max-w-content">
      <PageHeader
        title="Career Brain"
        description="Search your resumes, profile, and career history from one place. Ask questions about your career data."
        action={<Button onClick={rebuildIndex} disabled={indexing}>{indexing ? 'Indexing...' : 'Refresh knowledge'}</Button>}
      />
      <Card className="mb-5">
        <form onSubmit={search} className="flex flex-col gap-3 sm:flex-row">
          <Input aria-label="Career Brain search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about your skills, experience, or goals" />
          <div className="flex gap-2">
            <Button type="submit" disabled={searching || !query.trim()}>{searching ? 'Searching...' : 'Search'}</Button>
            <Button type="button" onClick={ask} disabled={searching || !query.trim()} variant="primary">{searching ? 'Answering...' : 'Ask Career Brain'}</Button>
            <Button type="button" variant="secondary" onClick={() => void buildContext()} disabled={searching || !query.trim()}>Build context</Button>
          </div>
        </form>
      </Card>
      {error && <ErrorState message={error} onRetry={() => void ask()} className="mb-5" />}
      {message && <p className="mb-5 rounded-md border border-surface-border bg-surface-muted p-3 text-body-sm text-text-muted" role="status">{message}</p>}
      {modelInfo && (
        <div className="flex items-center gap-3 mb-5 p-3 rounded-lg bg-surface-muted border border-surface-border">
          <span className="text-caption text-text-muted">Model:</span>
          <span className="text-body-sm text-text-secondary font-medium">{modelInfo.model}</span>
          <span className="text-caption text-text-muted">Confidence:</span>
          {confidenceBadge(modelInfo.confidence)}
        </div>
      )}
      {answer && (
        <Card className="mb-5">
          <h2 className="text-h3 text-text-primary">AI Answer</h2>
          <div className="mt-3 whitespace-pre-wrap text-body text-text-secondary">{answer}</div>
          {answerSources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-surface-border">
              <p className="text-label text-text-secondary">Sources:</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {answerSources.map((source) => (
                  <Badge key={`${source.source_type}-${source.id}`} variant="primary" size="sm">
                    {source.title || source.source_type}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}
      {context && (
        <Card className="mb-5">
          <h2 className="text-h3 text-text-primary">Retrieved career context</h2>
          <pre className="mt-3 whitespace-pre-wrap text-body text-text-secondary">{context}</pre>
        </Card>
      )}
      <div className="space-y-3">
        {results.map((result) => (
          <Card key={result.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-h3 text-text-primary">{result.title || result.source_type}</h2>
                <p className="mt-2 whitespace-pre-line text-body text-text-secondary">{result.content}</p>
              </div>
              <span className="shrink-0 text-caption text-text-muted">{Math.round(result.score * 100)}%</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

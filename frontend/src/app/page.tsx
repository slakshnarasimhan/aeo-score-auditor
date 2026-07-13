"use client";

import { FormEvent, useMemo, useState } from 'react';
import { ArrowLeft, Check, FileText, Loader2, Mail, Send, Sparkles } from 'lucide-react';
import { FORMAT_DEFINITIONS } from '@/lib/social-agents/formats';
import { GeneratedFormat, SocialFormat, SourceArticle } from '@/lib/social-agents/types';

type Step = 'compose' | 'results';

interface GenerateResponse {
  source: SourceArticle;
  outputs: GeneratedFormat[];
  failures?: { format: SocialFormat; error: string }[];
  error?: string;
}

const DEFAULT_FORMATS: SocialFormat[] = ['linkedin', 'powerpoint', 'instagram', 'x'];

export default function Home() {
  const [step, setStep] = useState<Step>('compose');
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [text, setText] = useState('');
  const [selectedFormats, setSelectedFormats] = useState<SocialFormat[]>(DEFAULT_FORMATS);
  const [source, setSource] = useState<SourceArticle | null>(null);
  const [outputs, setOutputs] = useState<GeneratedFormat[]>([]);
  const [activeFormat, setActiveFormat] = useState<SocialFormat>('linkedin');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [reviewOpen, setReviewOpen] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState('');

  const activeOutput = useMemo(
    () => outputs.find((output) => output.format === activeFormat) || outputs[0],
    [activeFormat, outputs],
  );

  const toggleFormat = (format: SocialFormat) => {
    setSelectedFormats((current) => (
      current.includes(format)
        ? current.filter((item) => item !== format)
        : [...current, format]
    ));
  };

  const generate = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setNotice('');

    if (!url.trim() && !text.trim()) {
      setError('Paste an article URL or the full article text.');
      return;
    }

    if (selectedFormats.length === 0) {
      setError('Choose at least one output format.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/social/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          url,
          text,
          formats: selectedFormats,
        }),
      });

      const data = await response.json() as GenerateResponse;
      if (!response.ok) {
        throw new Error(data.error || 'Generation failed.');
      }

      setSource(data.source);
      setOutputs(data.outputs);
      setActiveFormat(data.outputs[0]?.format || selectedFormats[0]);
      setStep('results');

      if (data.failures?.length) {
        setNotice(`Generated ${data.outputs.length} format(s). ${data.failures.length} format(s) need another try.`);
      }
    } catch (err: any) {
      setError(err?.message || 'Generation failed.');
    } finally {
      setLoading(false);
    }
  };

  const updateOutput = (format: SocialFormat, content: string) => {
    setOutputs((current) => current.map((output) => (
      output.format === format ? { ...output, content } : output
    )));
  };

  const submitForReview = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setNotice('');

    if (!source) {
      setError('Generate content before submitting for review.');
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch('/api/social/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipientEmail,
          source,
          outputs,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Could not send review email.');
      }

      setReviewOpen(false);
      setRecipientEmail('');
      setNotice('Review email sent successfully.');
    } catch (err: any) {
      setError(err?.message || 'Could not send review email.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-950">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 py-6 sm:px-8 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              Agent-backed content studio
            </p>
            <h1 className="mt-2 font-display text-4xl font-semibold text-slate-950 sm:text-5xl">
              Article to Social
            </h1>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
            <Sparkles className="h-4 w-4 text-slate-900" />
            Real OpenAI generation + Resend review email
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
        {step === 'compose' ? (
          <form onSubmit={generate} className="grid gap-8 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
            <div className="space-y-5">
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <div className="mb-5 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-950 text-white">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold">Source article</h2>
                    <p className="text-sm text-slate-500">Use a URL, paste the article, or provide both.</p>
                  </div>
                </div>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Working title</span>
                  <input
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Optional title for the review email"
                    className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  />
                </label>

                <label className="mt-5 block">
                  <span className="text-sm font-medium text-slate-700">Article URL</span>
                  <input
                    value={url}
                    onChange={(event) => setUrl(event.target.value)}
                    placeholder="https://example.com/long-form-article"
                    className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  />
                </label>

                <label className="mt-5 block">
                  <span className="text-sm font-medium text-slate-700">Pasted article text</span>
                  <textarea
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    placeholder="Paste the full long-form article here..."
                    rows={16}
                    className="mt-2 w-full resize-y rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm leading-6 outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                  />
                </label>
              </div>
            </div>

            <aside className="space-y-5">
              <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-xl font-semibold">Output formats</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Each checked format runs through its own skill.
                </p>

                <div className="mt-5 space-y-3">
                  {FORMAT_DEFINITIONS.map((format) => (
                    <label
                      key={format.id}
                      className="flex cursor-pointer gap-3 rounded-lg border border-slate-200 p-4 transition hover:border-slate-400"
                    >
                      <input
                        type="checkbox"
                        checked={selectedFormats.includes(format.id)}
                        onChange={() => toggleFormat(format.id)}
                        className="mt-1 h-4 w-4 rounded border-slate-300 text-slate-950 focus:ring-slate-900"
                      />
                      <span>
                        <span className="flex items-center gap-2 font-semibold">
                          <span
                            className="flex h-7 w-7 items-center justify-center rounded-md text-xs text-white"
                            style={{ backgroundColor: format.accent }}
                          >
                            {format.shortLabel}
                          </span>
                          {format.label}
                        </span>
                        <span className="mt-2 block text-sm leading-5 text-slate-500">
                          {format.description}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              {notice && (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                  {notice}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-950 px-5 py-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {loading ? 'Generating with agents...' : 'Generate'}
              </button>
            </aside>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
              <div>
                <button
                  type="button"
                  onClick={() => setStep('compose')}
                  className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-950"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to source
                </button>
                <h2 className="text-2xl font-semibold">{source?.title || 'Generated social content'}</h2>
                <p className="mt-1 max-w-3xl text-sm text-slate-500">
                  Edit each generated format below, then submit the final version for email review.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setReviewOpen(true)}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                <Send className="h-4 w-4" />
                Submit to Review
              </button>
            </div>

            {notice && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                {notice}
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
              <nav className="space-y-2">
                {outputs.map((output) => {
                  const definition = FORMAT_DEFINITIONS.find((format) => format.id === output.format);
                  const isActive = activeOutput?.format === output.format;
                  return (
                    <button
                      key={output.format}
                      type="button"
                      onClick={() => setActiveFormat(output.format)}
                      className={`w-full rounded-lg border p-4 text-left transition ${
                        isActive
                          ? 'border-slate-950 bg-white shadow-sm'
                          : 'border-slate-200 bg-white hover:border-slate-400'
                      }`}
                    >
                      <span className="flex items-center gap-2 font-semibold">
                        <span
                          className="flex h-7 w-7 items-center justify-center rounded-md text-xs text-white"
                          style={{ backgroundColor: definition?.accent || '#111827' }}
                        >
                          {definition?.shortLabel || output.format}
                        </span>
                        {definition?.label || output.format}
                      </span>
                      <span className="mt-2 block text-sm text-slate-500">{output.title}</span>
                    </button>
                  );
                })}
              </nav>

              {activeOutput && (
                <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="mb-5 border-b border-slate-200 pb-5">
                    <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {FORMAT_DEFINITIONS.find((format) => format.id === activeOutput.format)?.label}
                    </p>
                    <h3 className="mt-2 text-2xl font-semibold">{activeOutput.title}</h3>
                    <p className="mt-2 text-sm text-slate-500">{activeOutput.summary}</p>
                  </div>

                  {activeOutput.details.length > 0 && (
                    <div className="mb-5 grid gap-2 sm:grid-cols-2">
                      {activeOutput.details.map((detail) => (
                        <div key={detail} className="flex gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                          {detail}
                        </div>
                      ))}
                    </div>
                  )}

                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">Editable final content</span>
                    <textarea
                      value={activeOutput.content}
                      onChange={(event) => updateOutput(activeOutput.format, event.target.value)}
                      rows={22}
                      className="mt-2 w-full resize-y rounded-lg border border-slate-300 bg-white px-4 py-3 font-mono text-sm leading-6 outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                    />
                  </label>
                </article>
              )}
            </div>
          </div>
        )}
      </section>

      {reviewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-5">
          <form onSubmit={submitForReview} className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-slate-950 text-white">
              <Mail className="h-5 w-5" />
            </div>
            <h2 className="mt-4 text-2xl font-semibold">Send for review</h2>
            <p className="mt-2 text-sm text-slate-500">
              The recipient will receive the original source, format details, and your edited content.
            </p>

            <label className="mt-5 block">
              <span className="text-sm font-medium text-slate-700">Recipient email</span>
              <input
                type="email"
                value={recipientEmail}
                onChange={(event) => setRecipientEmail(event.target.value)}
                placeholder="reviewer@example.com"
                required
                className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
              />
            </label>

            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={() => setReviewOpen(false)}
                className="flex-1 rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Send
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
}

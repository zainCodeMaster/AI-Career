import type { ReactNode } from 'react';

interface AuthShellProps {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
  footer: ReactNode;
}

export function AuthShell({ eyebrow, title, description, children, footer }: AuthShellProps) {
  return (
    <main className="relative flex min-h-screen overflow-hidden bg-neutral-950 px-4 py-6 sm:px-8">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(14,165,233,0.28),_transparent_38%),radial-gradient(circle_at_bottom_left,_rgba(37,99,235,0.22),_transparent_42%)]" />
      <div className="relative mx-auto grid w-full max-w-6xl items-center gap-10 lg:grid-cols-[1fr_440px] lg:gap-20">
        <section className="hidden text-white lg:block">
          <div className="mb-10 flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-sky-400 text-lg font-bold text-neutral-950">C</div>
            <span className="text-lg font-semibold tracking-tight">CareerOS</span>
          </div>
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-sky-300">{eyebrow}</p>
          <h1 className="max-w-xl text-5xl font-semibold leading-tight tracking-tight">Build a career that moves with you.</h1>
          <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">Discover better opportunities, sharpen your profile, and keep every application in one intelligent workspace.</p>
          <div className="mt-10 flex gap-8 text-sm text-slate-300">
            <span><strong className="block text-2xl text-white">01</strong>Career profile</span>
            <span><strong className="block text-2xl text-white">02</strong>Job intelligence</span>
            <span><strong className="block text-2xl text-white">03</strong>Application CRM</span>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white p-6 shadow-2xl shadow-slate-950/30 sm:p-9">
          <div className="mb-8 lg:hidden">
            <div className="mb-6 flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-blue-600 font-bold text-white">C</div>
              <span className="font-semibold text-neutral-900">CareerOS</span>
            </div>
          </div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">{eyebrow}</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-neutral-950">{title}</h2>
          <p className="mt-3 text-sm leading-6 text-neutral-500">{description}</p>
          <div className="mt-8">{children}</div>
          <div className="mt-6 border-t border-neutral-100 pt-5 text-sm text-neutral-500">{footer}</div>
        </section>
      </div>
    </main>
  );
}

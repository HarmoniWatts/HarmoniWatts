import { Component, ElementRef, HostListener, inject, input, signal } from '@angular/core';

export interface InfoTipTermino {
  titulo: string;
  texto: string;
}

let nextId = 0;

/**
 * Botón informativo "i": muestra una explicación breve al hacer clic (o al enfocar
 * con teclado y pulsar Enter). Se cierra con Escape o al hacer clic fuera.
 */
@Component({
  selector: 'app-info-tip',
  standalone: true,
  template: `
    <!-- span con role="button" (no <button>): dentro de un <label> no roba la asociación con su campo -->
    <span
      class="it-btn"
      role="button"
      tabindex="0"
      [attr.aria-label]="'Qué es: ' + termino().titulo"
      [attr.aria-expanded]="open()"
      [attr.aria-controls]="panelId"
      (click)="toggle($event)"
      (keydown.enter)="toggle($event)"
      (keydown.space)="toggle($event)"
    >
      i
    </span>
    @if (open()) {
      <div class="it-panel" [class.it-panel-left]="alignLeft()" role="tooltip" [id]="panelId">
        <strong class="it-title">{{ termino().titulo }}</strong>
        <p class="it-text">{{ termino().texto }}</p>
      </div>
    }
  `,
  styles: `
    :host {
      position: relative;
      display: inline-flex;
      vertical-align: middle;
      margin-left: 0.35rem;
    }
    .it-btn {
      width: 1.15rem;
      height: 1.15rem;
      border-radius: 50%;
      border: 1px solid var(--color-border-input);
      background: var(--color-surface-2);
      color: var(--color-text-muted);
      font: italic 700 0.7rem/1 Georgia, serif;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      padding: 0;
      user-select: none;
    }
    .it-btn:hover,
    .it-btn[aria-expanded='true'] {
      border-color: var(--color-accent-border);
      color: var(--color-accent);
      background: var(--color-accent-soft);
    }
    .it-btn:focus-visible {
      outline: 2px solid var(--color-accent);
      outline-offset: 2px;
    }
    .it-panel {
      position: absolute;
      top: calc(100% + 0.4rem);
      left: 50%;
      transform: translateX(-50%);
      z-index: 50;
      width: min(18rem, calc(100vw - 2rem));
      border-radius: 0.6rem;
      border: 1px solid var(--color-border-strong);
      background: var(--color-surface-panel);
      box-shadow: var(--shadow-card);
      padding: 0.65rem 0.75rem;
      text-align: left;
      font-weight: 400;
      letter-spacing: normal;
      text-transform: none;
    }
    .it-panel-left {
      left: auto;
      right: -0.5rem;
      transform: none;
    }
    .it-title {
      display: block;
      font-size: 0.8rem;
      color: var(--color-text-strong);
      margin-bottom: 0.25rem;
    }
    .it-text {
      margin: 0;
      font-size: 0.78rem;
      line-height: 1.45;
      color: var(--color-text);
      white-space: normal;
    }
  `,
})
export class InfoTipComponent {
  private readonly host = inject(ElementRef<HTMLElement>);

  readonly termino = input.required<InfoTipTermino>();
  /** Abre el panel hacia la izquierda (para botones cerca del borde derecho). */
  readonly alignLeft = input(false);

  readonly open = signal(false);
  readonly panelId = `info-tip-${nextId++}`;

  toggle(event: Event): void {
    // preventDefault: que el clic no active el campo del <label> contenedor ni haga scroll con Espacio
    event.preventDefault();
    event.stopPropagation();
    this.open.update((v) => !v);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    if (this.open() && !this.host.nativeElement.contains(event.target as Node)) {
      this.open.set(false);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.open.set(false);
  }
}

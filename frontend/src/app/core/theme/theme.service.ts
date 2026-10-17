/**
 * Tema visual de la aplicación: oscuro / claro.
 *
 * Arquitectura:
 *   - Puerto: API pública del servicio (signal `theme()`, `toggle()`, `set()`).
 *   - Adaptador (este servicio): persiste en localStorage y aplica el atributo
 *     `data-theme` sobre <html>, que es el que consumen los tokens en
 *     `src/styles/tokens.css`.
 *
 * El estado inicial intenta leer la preferencia previa, y si no existe usa la
 * preferencia del sistema (`prefers-color-scheme`).
 */

import { Injectable, signal } from '@angular/core';

export type AppTheme = 'dark' | 'light';

const STORAGE_KEY = 'harmoniwatts.theme';
const DOM_ATTR = 'data-theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly _theme = signal<AppTheme>(this.resolveInitialTheme());

  readonly theme = this._theme.asReadonly();

  constructor() {
    this.applyToDom(this._theme());
  }

  toggle(): void {
    this.set(this._theme() === 'dark' ? 'light' : 'dark');
  }

  set(theme: AppTheme): void {
    if (theme !== 'dark' && theme !== 'light') {
      return;
    }
    this._theme.set(theme);
    this.applyToDom(theme);
    this.persist(theme);
  }

  private resolveInitialTheme(): AppTheme {
    const stored = this.readStored();
    if (stored) {
      return stored;
    }
    if (typeof window !== 'undefined' && window.matchMedia) {
      const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
      return prefersLight ? 'light' : 'dark';
    }
    return 'dark';
  }

  private readStored(): AppTheme | null {
    try {
      const v = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
      return v === 'dark' || v === 'light' ? v : null;
    } catch {
      return null;
    }
  }

  private persist(theme: AppTheme): void {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      /* almacenamiento no disponible: el cambio queda sólo en memoria */
    }
  }

  private applyToDom(theme: AppTheme): void {
    if (typeof document === 'undefined') {
      return;
    }
    document.documentElement.setAttribute(DOM_ATTR, theme);
    document.documentElement.style.colorScheme = theme;
  }
}

import React from 'react';
import { render } from '@testing-library/react';
import LoadingSpinner from '../components/common/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renderiza el SVG del spinner', () => {
    const { container } = render(<LoadingSpinner />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass('animate-spin');
  });

  it('en modo fullScreen envuelve en contenedor centrado', () => {
    const { container } = render(<LoadingSpinner fullScreen />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('min-h-screen');
    expect(wrapper).toHaveClass('flex');
    expect(wrapper).toHaveClass('items-center');
    expect(wrapper).toHaveClass('justify-center');
  });

  it('sin fullScreen no tiene contenedor de pantalla completa', () => {
    const { container } = render(<LoadingSpinner />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.tagName).toBe('svg');
  });

  it('aplica tamaño sm correctamente', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveClass('h-4');
    expect(svg).toHaveClass('w-4');
  });

  it('aplica tamaño lg correctamente', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveClass('h-12');
    expect(svg).toHaveClass('w-12');
  });

  it('tamaño por defecto es md', () => {
    const { container } = render(<LoadingSpinner />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveClass('h-8');
    expect(svg).toHaveClass('w-8');
  });
});

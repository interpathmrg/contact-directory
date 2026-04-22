import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Pagination from '../components/common/Pagination';

const defaultProps = {
  currentPage: 1,
  totalPages: 5,
  pageSize: 20,
  total: 100,
  onPageChange: jest.fn(),
  onPageSizeChange: jest.fn(),
};

beforeEach(() => {
  jest.clearAllMocks();
});

describe('Pagination', () => {
  it('muestra el rango y total correctamente', () => {
    render(<Pagination {...defaultProps} currentPage={2} pageSize={20} total={95} />);
    expect(screen.getByText(/21–40/)).toBeInTheDocument();
    expect(screen.getByText(/95/)).toBeInTheDocument();
  });

  it('deshabilita botón anterior en la primera página', () => {
    render(<Pagination {...defaultProps} currentPage={1} />);
    expect(screen.getByText('‹')).toBeDisabled();
    expect(screen.getByText('«')).toBeDisabled();
  });

  it('deshabilita botón siguiente en la última página', () => {
    render(<Pagination {...defaultProps} currentPage={5} totalPages={5} />);
    expect(screen.getByText('›')).toBeDisabled();
    expect(screen.getByText('»')).toBeDisabled();
  });

  it('llama onPageChange con página siguiente al hacer clic en ›', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} currentPage={2} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByText('›'));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });

  it('llama onPageChange con página anterior al hacer clic en ‹', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} currentPage={3} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByText('‹'));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('llama onPageChange(1) al hacer clic en «', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} currentPage={4} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByText('«'));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it('llama onPageChange(totalPages) al hacer clic en »', () => {
    const onPageChange = jest.fn();
    render(<Pagination {...defaultProps} currentPage={2} totalPages={8} onPageChange={onPageChange} />);
    fireEvent.click(screen.getByText('»'));
    expect(onPageChange).toHaveBeenCalledWith(8);
  });

  it('llama onPageSizeChange al cambiar el selector de tamaño', () => {
    const onPageSizeChange = jest.fn();
    render(<Pagination {...defaultProps} onPageSizeChange={onPageSizeChange} />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '50' } });
    expect(onPageSizeChange).toHaveBeenCalledWith(50);
  });

  it('marca la página actual con estilo activo', () => {
    render(<Pagination {...defaultProps} currentPage={3} totalPages={5} />);
    const page3Btn = screen.getByText('3');
    expect(page3Btn).toHaveClass('bg-primary-600');
  });
});

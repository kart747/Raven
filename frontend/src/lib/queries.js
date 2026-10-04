import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { apiGet } from '../api';

// One hook per API resource so caching and loading/error states are shared across components.

export const useParties = () =>
  useQuery({ queryKey: ['parties'], queryFn: () => apiGet('/api/v1/parties') });

export const useDashboardStats = (year) =>
  useQuery({ queryKey: ['donation-stats', year], queryFn: () => apiGet('/api/v1/donations/stats', { year }) });

export const useCandidateStateSummary = (house = 'Lok Sabha') =>
  useQuery({
    queryKey: ['candidate-state-summary', house],
    queryFn: () => apiGet('/api/v1/candidates/state-summary', { house }),
  });

export const useStateCandidates = (state, house = 'Lok Sabha') =>
  useQuery({
    queryKey: ['candidates', 'state', state, house],
    queryFn: () => apiGet('/api/v1/candidates', { state, house, sort_by: 'assets', limit: 200 }),
    enabled: !!state,
  });

export const useCandidates = (params) =>
  useQuery({
    queryKey: ['candidates', params],
    queryFn: () => apiGet('/api/v1/candidates', params),
    placeholderData: keepPreviousData,
  });

export const useElections = () =>
  useQuery({ queryKey: ['elections'], queryFn: () => apiGet('/api/v1/candidates/elections') });

export const useStateNgoSummary = (state) =>
  useQuery({
    queryKey: ['ngo-state-summary', state],
    queryFn: () => apiGet(`/api/v1/ngos/state-summary/${encodeURIComponent(state)}`),
    enabled: !!state,
  });

export const useStateLegislative = (state) =>
  useQuery({
    queryKey: ['legislative-state', state],
    queryFn: () => apiGet(`/api/v1/legislative/state/${encodeURIComponent(state)}`),
    enabled: !!state,
  });

export const usePibReleases = () =>
  useQuery({
    queryKey: ['pib'],
    queryFn: () => apiGet('/api/v1/pib/releases', { limit: 10 }),
    refetchInterval: 15 * 60 * 1000,
  });

export const useNgoStats = () =>
  useQuery({ queryKey: ['ngo-stats'], queryFn: () => apiGet('/api/v1/ngos/stats') });

export const useNgos = (params) =>
  useQuery({
    queryKey: ['ngos', params],
    queryFn: () => apiGet('/api/v1/ngos', params),
    placeholderData: keepPreviousData,
  });

export const useNgoDonations = (params) =>
  useQuery({
    queryKey: ['ngo-donations', params],
    queryFn: () => apiGet('/api/v1/ngo-donations', params),
    placeholderData: keepPreviousData,
  });

export const useNgoDetail = (id) =>
  useQuery({ queryKey: ['ngo', id], queryFn: () => apiGet(`/api/v1/ngos/${id}`), enabled: id != null });

export const useDonorProfile = (id) =>
  useQuery({ queryKey: ['donor', id], queryFn: () => apiGet(`/api/v1/donors/${id}`), enabled: id != null });

export const useDataQuality = () =>
  useQuery({ queryKey: ['data-quality'], queryFn: () => apiGet('/api/v1/data-quality') });

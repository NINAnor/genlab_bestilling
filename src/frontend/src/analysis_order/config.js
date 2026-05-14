import axios from 'axios';

export const config = JSON.parse(document.getElementById('initial-data').textContent);

export const client = axios.create({
  headers: {
    'X-CSRFToken': config.csrf,
  },
});

export const EXTRACTION_STATUS_OPTIONS = [
  { value: 'marked', label: 'Marked' },
  { value: 'plucked', label: 'Plucked' },
  { value: 'isolated', label: 'Isolated' },
];

export interface User {
  id: string;
  name: string;
  email: string;
  avatar_url: string;
  role: 'user' | 'admin';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
  total: number | null;
}

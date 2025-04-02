export const USER_ID_KEY = 'xmemory_user_id';

export const getUserID = (): string | null => {
  return localStorage.getItem(USER_ID_KEY);
};

export const setUserID = (user_id: string): void => {
  localStorage.setItem(USER_ID_KEY, user_id);
};

export const clearUserID = (): void => {
  localStorage.removeItem(USER_ID_KEY);
}; 
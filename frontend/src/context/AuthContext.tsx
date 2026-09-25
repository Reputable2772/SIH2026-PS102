import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import { UserProfile } from '../types';

export interface DynamicPersonaPayload {
  persona_id?: string;
  role?: 'CENTRAL_AUDITOR' | 'STATE_NODAL_OFFICER' | 'DISTRICT_AUTHORITY' | 'MP_USER' | 'CITIZEN';
  state?: string;
  district?: string;
  mp_name?: string;
  constituency?: string;
  strict_isolation?: boolean;
}

interface AuthContextType {
  currentUser: UserProfile | null;
  activePersonaId: string;
  personas: Record<string, UserProfile>;
  switchPersona: (personaId: string) => Promise<void>;
  switchDynamicPersona: (payload: DynamicPersonaPayload) => Promise<void>;
  authFetch: (url: string, options?: RequestInit) => Promise<Response>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [activePersonaId, setActivePersonaId] = useState<string>('central_auditor');
  const [personas, setPersonas] = useState<Record<string, UserProfile>>({});
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      try {
        const fetchedPersonas = await api.getPersonas();
        setPersonas(fetchedPersonas);

        const savedToken = localStorage.getItem('mplads_auth_token');
        const savedPersona = localStorage.getItem('mplads_persona_id');
        const savedPayloadStr = localStorage.getItem('mplads_persona_payload');

        if (savedToken && savedPayloadStr) {
          try {
            const payload = JSON.parse(savedPayloadStr);
            const res = await api.switchPersona(payload);
            api.setToken(res.access_token);
            setCurrentUser(res.user);
            setActivePersonaId(savedPersona || res.user.role.toLowerCase());
            return;
          } catch (e) {
            console.warn('Failed to restore saved persona session:', e);
          }
        }

        // Default to central auditor
        const res = await api.switchPersona('central_auditor');
        api.setToken(res.access_token);
        localStorage.setItem('mplads_auth_token', res.access_token);
        localStorage.setItem('mplads_persona_id', 'central_auditor');
        localStorage.setItem('mplads_persona_payload', JSON.stringify({ persona_id: 'central_auditor' }));
        setCurrentUser(res.user);
        setActivePersonaId('central_auditor');
      } catch (err) {
        console.error('Failed to initialize demo personas:', err);
      } finally {
        setLoading(false);
      }
    }
    initAuth();
  }, []);

  const switchDynamicPersona = async (payload: DynamicPersonaPayload) => {
    setLoading(true);
    try {
      const res = await api.switchPersona(payload);
      api.setToken(res.access_token);
      const pid = payload.persona_id || res.user.role.toLowerCase();
      localStorage.setItem('mplads_auth_token', res.access_token);
      localStorage.setItem('mplads_persona_id', pid);
      localStorage.setItem('mplads_persona_payload', JSON.stringify(payload));
      setCurrentUser(res.user);
      setActivePersonaId(pid);
    } catch (err) {
      console.error('Failed to switch dynamic persona:', err);
    } finally {
      setLoading(false);
    }
  };

  const switchPersona = async (personaId: string) => {
    await switchDynamicPersona({ persona_id: personaId });
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        activePersonaId,
        personas,
        switchPersona,
        switchDynamicPersona,
        authFetch: (url: string, opts?: RequestInit) => api.authFetch(url, opts),
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export interface Location {
  id: string;
  name: string;
  description: string | null;
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  accuracy_meters: number | null;
  country: string | null;
  province: string | null;
  city: string | null;
  address_text: string | null;
  building: string | null;
  floor: string | null;
  zone: string | null;
  rack: string | null;
  position: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

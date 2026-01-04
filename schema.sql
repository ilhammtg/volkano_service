-- 2️⃣ ENUM level aktivitas
CREATE TYPE volcano_level AS ENUM (
  'Normal',
  'Waspada',
  'Siaga',
  'Awas'
);

-- 3️⃣ Tabel master gunung api
CREATE TABLE volcanoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  province TEXT,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),

  CONSTRAINT volcano_unique_name UNIQUE (name)
);

-- 4️⃣ Tabel status TERKINI
CREATE TABLE volcano_status_current (
  volcano_id UUID PRIMARY KEY REFERENCES volcanoes(id) ON DELETE CASCADE,
  level volcano_level NOT NULL,
  status_text TEXT,
  source TEXT DEFAULT 'PVMBG/MAGMA',
  observed_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 5️⃣ Tabel histori perubahan status
CREATE TABLE volcano_status_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  volcano_id UUID REFERENCES volcanoes(id) ON DELETE CASCADE,
  level volcano_level NOT NULL,
  status_text TEXT,
  source TEXT DEFAULT 'PVMBG/MAGMA',
  observed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 6️⃣ Index
CREATE INDEX idx_volcanoes_location ON volcanoes (latitude, longitude);
CREATE INDEX idx_status_current_level ON volcano_status_current (level);
CREATE INDEX idx_status_history_volcano ON volcano_status_history (volcano_id);

-- 7️⃣ Extension GEO (Optional)
CREATE EXTENSION IF NOT EXISTS postgis;

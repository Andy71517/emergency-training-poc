import { Canvas, useFrame } from "@react-three/fiber";
import { CuboidCollider, Physics, RigidBody, type RapierRigidBody } from "@react-three/rapier";
import { ArrowLeft, RotateCcw, Play, ShieldCheck } from "lucide-react";
import { Suspense, useEffect, useRef, useState } from "react";

type Vec3 = { x: number; y: number; z: number };
type Quat = { x: number; y: number; z: number; w: number };
type Configuration = {
  contract_version: string;
  proof_id: string;
  scenario_id: string;
  object_id: string;
  gravity_mps2: Vec3;
  fixed_timestep_seconds: number;
  object_mass_kg: number;
  linear_damping: number;
  angular_damping: number;
  chair_material: { friction: number; restitution: number };
  floor_material: { friction: number; restitution: number };
  initial_transform: { position_m: Vec3; rotation: Quat };
  chair_colliders: { collider_id: string; center_m: Vec3; half_extents_m: Vec3 }[];
  static_colliders: { collider_id: string; center_m: Vec3; half_extents_m: Vec3 }[];
  acceptance: {
    minimum_horizontal_movement_m: number;
    maximum_observation_seconds: number;
    required_contact_object_id: string;
    settle_linear_speed_mps: number;
    settle_angular_speed_radps: number;
    settle_duration_seconds: number;
  };
};
type Command = {
  command_id: string;
  session_id: string;
  scenario_id: string;
  proof_id: string;
  object_id: string;
  impulse_ns: Vec3;
  application_point_m: Vec3;
};
type Result = {
  accepted: boolean;
  summary: string;
  checks: string[];
};
type Observation = {
  contract_version: string;
  command_id: string;
  session_id: string;
  scenario_id: string;
  proof_id: string;
  object_id: string;
  engine: { client_name: string; engine_name: string; engine_version: string };
  started_at: string;
  completed_at: string;
  elapsed_seconds: number;
  initial_transform: { position_m: Vec3; rotation: Quat };
  final_transform: { position_m: Vec3; rotation: Quat };
  horizontal_displacement_m: number;
  minimum_floor_clearance_m: number;
  contacts: { object_id: string; contacted_object_id: string; first_contact_seconds: number }[];
  settled: boolean;
  evidence_notes: string[];
};

const vector = (v: Vec3): [number, number, number] => [v.x, v.y, v.z];
const errorMessage = (error: unknown) => error instanceof Error ? error.message : "The physics run failed.";
const initialStatus = "Ready";

export function PhysicsLab({ onBack }: { onBack: () => void }) {
  const [config, setConfig] = useState<Configuration | null>(null);
  const [status, setStatus] = useState(initialStatus);
  const [error, setError] = useState("");
  const [command, setCommand] = useState<Command | null>(null);
  const [runKey, setRunKey] = useState(0);
  const [busy, setBusy] = useState(false);
  const [debug, setDebug] = useState(false);
  const [observation, setObservation] = useState<Observation | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    fetch("/api/physics/proof/configuration")
      .then((response) => {
        if (!response.ok) throw new Error("The backend physics configuration is unavailable.");
        return response.json() as Promise<Configuration>;
      })
      .then(setConfig)
      .catch((caught: unknown) => setError(errorMessage(caught)));
  }, []);

  const reset = () => {
    setCommand(null);
    setObservation(null);
    setResult(null);
    setError("");
    setBusy(false);
    setStatus(initialStatus);
    setRunKey((value) => value + 1);
  };

  const run = async () => {
    if (!config || busy || command) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/physics/proof/authorize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: `physics-${crypto.randomUUID()}`,
          scenario_id: config.scenario_id,
        }),
      });
      if (!response.ok) throw new Error("The backend did not authorize the interaction.");
      setStatus("Authorized · applying impulse");
      setCommand(await response.json() as Command);
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(false);
    }
  };

  const finish = async (evidence: Observation) => {
    setObservation(evidence);
    setStatus("Contact measured · saving evidence");
    try {
      const response = await fetch("/api/physics/proof/observations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(evidence),
      });
      if (!response.ok) throw new Error("The backend rejected the physics observation.");
      const verdict = await response.json() as Result;
      setResult(verdict);
      setStatus(verdict.accepted ? "Evidence saved · proof passed" : "Evidence saved · needs review");
    } catch (caught) {
      setError(errorMessage(caught));
      setStatus("Observation could not be saved");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="physics-shell min-h-screen bg-ink text-slate-100">
      <div className="technical-grid" />
      <div className="physics-frame relative mx-auto max-w-[1500px] px-5 py-6 sm:px-8 lg:px-10">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div>
            <p className="eyebrow text-azure-300">Visual development proof · primitive geometry</p>
            <h1 className="mt-1 font-display text-2xl font-semibold">Chair movement and contact</h1>
          </div>
          <button className="secondary-button" onClick={onBack} type="button"><ArrowLeft size={16} /> Session demo</button>
        </header>
        <div className="physics-layout">
          <section className="panel physics-viewport" aria-label="Interactive 3D physics scene">
            {config ? (
              <Canvas camera={{ position: [3.6, 2.5, 4.3], fov: 43 }} shadows>
                <color attach="background" args={["#091726"]} />
                <ambientLight intensity={1.1} />
                <directionalLight position={[-2, 6, 5]} intensity={2.2} castShadow shadow-mapSize={[1024, 1024]} />
                <gridHelper args={[6, 12, "#37627b", "#193246"]} position={[0, 0.004, 0]} />
                <Suspense fallback={null}>
                  <Physics key={runKey} gravity={vector(config.gravity_mps2)} timeStep={config.fixed_timestep_seconds} debug={debug}>
                    <PhysicsScene
                      config={config}
                      command={command}
                      onStatus={setStatus}
                      onFinish={(value) => void finish(value)}
                    />
                  </Physics>
                </Suspense>
              </Canvas>
            ) : <div className="physics-loading">Loading the backend scene configuration…</div>}
            <span className="physics-viewport-label">LIVE PHYSICS · THREE.JS + RAPIER</span>
          </section>
          <aside className="panel physics-controls">
            <p className="eyebrow text-amber-300">Bounded test</p>
            <h2 className="mt-2 font-display text-xl font-semibold">One chair. One impulse. Real collision.</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              The backend authorizes the interaction. Rapier simulates the chair and reports movement
              and contact. This primitive is a test fixture, not an AI generated asset or an Unreal scene.
            </p>
            <div className="physics-constants">
              <span>Mass <strong>{config?.object_mass_kg ?? "—"} kg</strong></span>
              <span>Gravity <strong>{config?.gravity_mps2.y ?? "—"} m/s²</strong></span>
              <span>Test <strong>{config?.proof_id ?? "Loading"}</strong></span>
            </div>
            <p className="physics-status"><span className="status-dot" /> {status}</p>
            {error && <p className="studio-error" role="alert">{error}</p>}
            <div className="mt-5 grid gap-2">
              <button className="run-button" type="button" disabled={!config || busy || !!command} onClick={() => void run()}>
                <Play size={18} fill="currentColor" /> Run physics proof
              </button>
              <button className="secondary-button" type="button" onClick={reset}><RotateCcw size={16} /> Reset scene</button>
            </div>
            <label className="physics-debug">
              <input type="checkbox" checked={debug} onChange={(event) => setDebug(event.target.checked)} />
              Show collision shapes
            </label>
            {observation && (
              <div className="physics-evidence" aria-live="polite">
                <p className="eyebrow text-azure-300"><ShieldCheck size={14} className="inline" /> Measured evidence</p>
                <div><span>Maximum movement</span><strong>{observation.horizontal_displacement_m.toFixed(2)} m</strong></div>
                <div><span>Barrier contact</span><strong>{observation.contacts.some((item) => item.contacted_object_id === "contact_barrier") ? "Detected" : "Not detected"}</strong></div>
                <div><span>Elapsed</span><strong>{observation.elapsed_seconds.toFixed(2)} s</strong></div>
                <div><span>Settled</span><strong>{observation.settled ? "Yes" : "No"}</strong></div>
                <p className={result?.accepted ? "physics-pass" : "physics-review"}>{result?.summary ?? "Sending to backend…"}</p>
                {result && <p className="text-xs text-slate-500">Command {observation.command_id}</p>}
              </div>
            )}
          </aside>
        </div>
      </div>
    </main>
  );
}

function PhysicsScene({
  config, command, onStatus, onFinish,
}: {
  config: Configuration;
  command: Command | null;
  onStatus: (status: string) => void;
  onFinish: (observation: Observation) => void;
}) {
  const body = useRef<RapierRigidBody | null>(null);
  const applied = useRef(false);
  const done = useRef(false);
  const started = useRef(0);
  const startedAt = useRef("");
  const firstContact = useRef<number | null>(null);
  const floorContact = useRef<number | null>(null);
  const maximumMovement = useRef(0);
  const minimumClearance = useRef(Number.POSITIVE_INFINITY);
  const settledSince = useRef<number | null>(null);

  useFrame(() => {
    if (!command || done.current || !body.current) return;
    const rigidBody = body.current;
    if (!applied.current) {
      applied.current = true;
      started.current = performance.now();
      startedAt.current = new Date().toISOString();
      const position = rigidBody.translation();
      rigidBody.applyImpulseAtPoint(command.impulse_ns, {
        x: position.x + command.application_point_m.x,
        y: position.y + command.application_point_m.y,
        z: position.z + command.application_point_m.z,
      }, true);
      return;
    }
    const elapsed = (performance.now() - started.current) / 1000;
    const position = rigidBody.translation();
    const rotation = rigidBody.rotation();
    const initial = config.initial_transform.position_m;
    const movement = Math.hypot(position.x - initial.x, position.z - initial.z);
    maximumMovement.current = Math.max(maximumMovement.current, movement);
    // Transform every corner of the compound collider to measure its lowest point.
    // The floor top is y=0; this is an approximate geometric clearance, not contact data.
    const q = rotation;
    for (const collider of config.chair_colliders) {
      for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
        const x = collider.center_m.x + sx * collider.half_extents_m.x;
        const y = collider.center_m.y + sy * collider.half_extents_m.y;
        const z = collider.center_m.z + sz * collider.half_extents_m.z;
        const ix = q.w * x + q.y * z - q.z * y;
        const iy = q.w * y + q.z * x - q.x * z;
        const iz = q.w * z + q.x * y - q.y * x;
        const iw = -q.x * x - q.y * y - q.z * z;
        const rotatedY = iy * q.w + iw * -q.y + iz * -q.x - ix * -q.z;
        minimumClearance.current = Math.min(minimumClearance.current, position.y + rotatedY);
      }
    }
    if (movement >= config.acceptance.minimum_horizontal_movement_m && firstContact.current === null) {
      onStatus("Movement detected · awaiting contact");
    }
    const velocity = rigidBody.linvel();
    const angular = rigidBody.angvel();
    const quiet = Math.hypot(velocity.x, velocity.y, velocity.z) < config.acceptance.settle_linear_speed_mps
      && Math.hypot(angular.x, angular.y, angular.z) < config.acceptance.settle_angular_speed_radps;
    settledSince.current = quiet ? (settledSince.current ?? elapsed) : null;
    const settled = settledSince.current !== null && elapsed - settledSince.current >= config.acceptance.settle_duration_seconds;
    if (!settled && elapsed < config.acceptance.maximum_observation_seconds) return;
    done.current = true;
    const contacts = [];
    if (firstContact.current !== null) contacts.push({
      object_id: config.object_id, contacted_object_id: "contact_barrier",
      first_contact_seconds: firstContact.current,
    });
    if (floorContact.current !== null) contacts.push({
      object_id: config.object_id, contacted_object_id: "floor",
      first_contact_seconds: floorContact.current,
    });
    onFinish({
      contract_version: config.contract_version,
      command_id: command.command_id,
      session_id: command.session_id,
      scenario_id: command.scenario_id,
      proof_id: command.proof_id,
      object_id: command.object_id,
      engine: { client_name: "browser-physics-lab", engine_name: "Rapier", engine_version: "0.19.2" },
      started_at: startedAt.current,
      completed_at: new Date().toISOString(),
      elapsed_seconds: elapsed,
      initial_transform: config.initial_transform,
      final_transform: { position_m: position, rotation },
      horizontal_displacement_m: maximumMovement.current,
      minimum_floor_clearance_m: minimumClearance.current,
      contacts,
      settled,
      evidence_notes: ["Primitive chair with compound box colliders; browser development proof."],
    });
  });

  const floor = config.static_colliders.find((item) => item.collider_id === "floor")!;
  const barrier = config.static_colliders.find((item) => item.collider_id === "contact_barrier")!;
  return (
    <>
      <RigidBody type="fixed" name="floor" colliders={false} friction={config.floor_material.friction}>
        <CuboidCollider args={vector(floor.half_extents_m)} position={vector(floor.center_m)} />
        <mesh position={vector(floor.center_m)} receiveShadow>
          <boxGeometry args={vector({ x: floor.half_extents_m.x * 2, y: floor.half_extents_m.y * 2, z: floor.half_extents_m.z * 2 })} />
          <meshStandardMaterial color="#1c3343" roughness={0.9} />
        </mesh>
      </RigidBody>
      <RigidBody type="fixed" name="contact_barrier" colliders={false}>
        <CuboidCollider
          args={vector(barrier.half_extents_m)} position={vector(barrier.center_m)}
          onCollisionEnter={() => {
            if (!applied.current || firstContact.current !== null) return;
            firstContact.current = (performance.now() - started.current) / 1000;
            onStatus("Contact detected · recording motion");
          }}
        />
        <mesh position={vector(barrier.center_m)} castShadow receiveShadow>
          <boxGeometry args={[barrier.half_extents_m.x * 2, barrier.half_extents_m.y * 2, barrier.half_extents_m.z * 2]} />
          <meshStandardMaterial color="#efb955" metalness={0.1} roughness={0.55} />
        </mesh>
      </RigidBody>
      <RigidBody
        ref={body} type="dynamic" name="chair" colliders={false}
        position={vector(config.initial_transform.position_m)}
        linearDamping={config.linear_damping}
        angularDamping={config.angular_damping} canSleep={false} ccd
        friction={config.chair_material.friction} restitution={config.chair_material.restitution}
        onCollisionEnter={({ other }) => {
          if (!applied.current || other.rigidBodyObject?.name !== "floor" || floorContact.current !== null) return;
          floorContact.current = (performance.now() - started.current) / 1000;
        }}
      >
        {config.chair_colliders.map((part) => {
          const totalVolume = config.chair_colliders.reduce((sum, collider) =>
            sum + collider.half_extents_m.x * collider.half_extents_m.y * collider.half_extents_m.z, 0);
          const volume = part.half_extents_m.x * part.half_extents_m.y * part.half_extents_m.z;
          return <CuboidCollider key={part.collider_id} args={vector(part.half_extents_m)} position={vector(part.center_m)}
            mass={config.object_mass_kg * volume / totalVolume}
            friction={config.chair_material.friction} restitution={config.chair_material.restitution} />;
        })}
        <group>
          {config.chair_colliders.map((part) => (
            <mesh key={part.collider_id} position={vector(part.center_m)} castShadow receiveShadow>
              <boxGeometry args={[part.half_extents_m.x * 2, part.half_extents_m.y * 2, part.half_extents_m.z * 2]} />
              <meshStandardMaterial color={part.collider_id === "seat" ? "#aa6650" : "#82503e"} roughness={0.7} />
            </mesh>
          ))}
        </group>
      </RigidBody>
    </>
  );
}

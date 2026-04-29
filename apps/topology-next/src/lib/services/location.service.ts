import type { ILocationRepository } from "@/lib/repositories/contracts";
import { LocationRepository } from "@/lib/repositories/location.repository";
import { NotFoundError, ValidationError } from "@/lib/errors/domain-errors";
import type { CreateLocationInput, UpdateLocationInput } from "@/lib/validators/location.schemas";

interface LocationServiceDeps {
  locationRepo?: ILocationRepository;
}

export class LocationService {
  private readonly locationRepo: ILocationRepository;

  constructor(deps: LocationServiceDeps = {}) {
    this.locationRepo = deps.locationRepo ?? new LocationRepository();
  }

  async create(input: CreateLocationInput) {
    if (!input.name.trim()) {
      throw new ValidationError("Location name is required");
    }
    return this.locationRepo.create(input);
  }

  async getById(id: string) {
    const location = await this.locationRepo.findById(id);
    if (!location) {
      throw new NotFoundError("Location not found");
    }
    return location;
  }

  async list() {
    return this.locationRepo.findAll();
  }

  async update(id: string, input: UpdateLocationInput) {
    const current = await this.locationRepo.findById(id);
    if (!current) {
      throw new NotFoundError("Location not found");
    }
    const updated = await this.locationRepo.update(id, input);
    if (!updated) {
      throw new NotFoundError("Location not found");
    }
    return updated;
  }
}

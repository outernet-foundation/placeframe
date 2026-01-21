#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::System {
class OperatingSystem;
}

namespace DotNet::System {

class Environment {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: Environment() = delete;
  private: static void* (*Property_get_OSVersion)(void** reinteropException);
  public: static ::DotNet::System::OperatingSystem OSVersion();
};

} // namespace DotNet::System



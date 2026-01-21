#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumMetadataType.h>
#include <DotNet/CesiumForUnity/CesiumMetadataComponentType.h>

namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}
namespace DotNet::CesiumForUnity {
enum class CesiumMetadataType;
}
namespace DotNet::CesiumForUnity {
enum class CesiumMetadataComponentType;
}

namespace DotNet::CesiumForUnity {

struct CesiumMetadataValueType {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_RFYaAjfQVfO4__8eI7fs9pw)(::std::uint32_t type, ::std::uint32_t componentType, ::std::uint8_t isArray, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException);
  public: static CesiumMetadataValueType Construct(::DotNet::CesiumForUnity::CesiumMetadataType type, ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType, bool isArray);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException);
  public: static CesiumMetadataValueType Construct();
  public: ::DotNet::CesiumForUnity::CesiumMetadataType type;
  public: ::DotNet::CesiumForUnity::CesiumMetadataComponentType componentType;
  public: bool isArray;
};

} // namespace DotNet::CesiumForUnity



#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include "TestGltfModelImpl.h"

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::CesiumForUnity {

class TestGltfModel {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit TestGltfModel(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: TestGltfModel(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: TestGltfModel();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_NativeImplementation)(void*);
  public: ::CesiumForUnityNative::TestGltfModelImpl& NativeImplementation() const noexcept;
};

} // namespace DotNet::CesiumForUnity



#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct uint3;
}

namespace DotNet::Unity::Mathematics {

struct uint3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_fwI58ky8hlqSzCrUJCqq4Q)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::DotNet::Unity::Mathematics::uint3* pReturnValue, void** reinteropException);
  public: static uint3 Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z);
  public: ::std::uint32_t x;
  public: ::std::uint32_t y;
  public: ::std::uint32_t z;
};

} // namespace DotNet::Unity::Mathematics



#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct uint4;
}

namespace DotNet::Unity::Mathematics {

struct uint4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_cx5C8OyRaFgckdYoG5u6cw)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w, ::DotNet::Unity::Mathematics::uint4* pReturnValue, void** reinteropException);
  public: static uint4 Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w);
  public: ::std::uint32_t x;
  public: ::std::uint32_t y;
  public: ::std::uint32_t z;
  public: ::std::uint32_t w;
};

} // namespace DotNet::Unity::Mathematics


